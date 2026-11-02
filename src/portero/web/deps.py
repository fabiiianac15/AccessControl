"""Dependencias de FastAPI: base de datos, sesión, CSRF y plantillas."""

from __future__ import annotations

import hmac
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from fastapi import Depends, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .. import __version__, crypto, ledger, policy, reports
from ..state import AppState

SESSION_COOKIE = "portero_session"
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


class LoginRequired(Exception):
    pass


def _local_time(ts: str | None, fmt: str, tz) -> str:
    return reports.to_local(ts, tz).strftime(fmt) if ts else "Nunca"


_DAYS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
_MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
    "octubre", "noviembre", "diciembre",
)  # fmt: skip


def long_date(moment: datetime) -> str:
    return f"{_DAYS[moment.weekday()]} {moment.day} de {_MONTHS[moment.month - 1]}"


def app_state(request: Request) -> AppState:
    return request.app.state.portero


def get_db(state: AppState = Depends(app_state)) -> Iterator[sqlite3.Connection]:
    with state.db() as conn:
        yield conn


@dataclass(frozen=True)
class Admin:
    id: int
    username: str
    role: str
    csrf_token: str


def current_admin(
    request: Request,
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Admin:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise LoginRequired
    row = conn.execute(
        """SELECT a.id, a.username, a.role, s.csrf_token, s.expires_at
           FROM sessions s JOIN admins a ON a.id = s.admin_id WHERE s.token_hash = ?""",
        (crypto.token_hash(token),),
    ).fetchone()
    if row is None or row["expires_at"] <= ledger.iso(state.clock()):
        raise LoginRequired
    admin = Admin(row["id"], row["username"], row["role"], row["csrf_token"])
    request.state.admin = admin
    return admin


def _check_csrf(admin: Admin, supplied: str | None) -> None:
    if not supplied or not hmac.compare_digest(admin.csrf_token, supplied):
        raise HTTPException(403, "Token CSRF inválido. Recarga la página.")


def _require_admin_role(admin: Admin) -> None:
    if admin.role != "admin":
        raise HTTPException(403, "Tu cuenta es de solo lectura.")


def form_member(admin: Admin = Depends(current_admin), csrf: str = Form(default="")) -> Admin:
    """Acciones sobre la propia cuenta: exige CSRF, sirve para cualquier rol."""
    _check_csrf(admin, csrf)
    return admin


def form_writer(admin: Admin = Depends(current_admin), csrf: str = Form(default="")) -> Admin:
    """Para formularios que modifican datos: exige CSRF y rol de administrador."""
    _check_csrf(admin, csrf)
    _require_admin_role(admin)
    return admin


def api_writer(
    admin: Admin = Depends(current_admin),
    x_csrf_token: str | None = Header(default=None),
) -> Admin:
    _check_csrf(admin, x_csrf_token)
    _require_admin_role(admin)
    return admin


def render(
    request: Request,
    name: str,
    status_code: int = 200,
    **context: object,
) -> HTMLResponse:
    state: AppState = request.app.state.portero
    tz = state.settings.tz
    base = {
        "org_name": state.settings.org_name,
        "version": __version__,
        "admin": getattr(request.state, "admin", None),
        "reasons": policy.REASONS,
        "local_time": lambda ts, fmt="%d/%m/%Y %H:%M": _local_time(ts, fmt, tz),
        "weekdays_label": policy.weekdays_label,
        "minutes_label": policy.minutes_label,
        "notice": NOTICES.get(request.query_params.get("m", "")),
    }
    return templates.TemplateResponse(request, name, {**base, **context}, status_code=status_code)


NOTICES = {
    "person_saved": "Datos guardados.",
    "person_erased": "Persona suprimida. Su historial quedó como seudónimo.",
    "consent_saved": "Autorización registrada.",
    "consent_revoked": "Autorización retirada y plantillas faciales borradas.",
    "faces_deleted": "Muestras faciales borradas.",
    "pin_removed": "PIN eliminado.",
    "grant_saved": "Permiso agregado.",
    "grant_deleted": "Permiso quitado.",
    "zone_saved": "Zona guardada.",
    "zone_deleted": "Zona eliminada.",
    "zone_in_use": "No se puede eliminar: tiene kioscos asociados.",
    "kiosk_saved": "Kiosco actualizado.",
    "kiosk_deleted": "Kiosco eliminado.",
    "password_changed": "Contraseña actualizada.",
    "password_bad": "La contraseña actual no coincide o la nueva tiene menos de 12 caracteres.",
    "grant_bad": "Revisa el permiso: elige zona, días y un horario válido.",
}
