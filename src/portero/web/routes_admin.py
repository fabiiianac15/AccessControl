"""Tablero, zonas y kioscos, eventos, asistencia, bitácora y privacidad."""

from __future__ import annotations

import re
import secrets
import sqlite3
from datetime import date, timedelta
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from .. import access, crypto, ledger, people, policy, reports
from ..state import AppState
from .charts import hourly_bars
from .deps import Admin, app_state, current_admin, form_writer, get_db, long_date, render

router = APIRouter()
_PHOTO_NAME = re.compile(r"^[0-9-]{10}-[0-9a-f]{32}\.enc$")


def _day(value: str, fallback: date) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return fallback


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    _: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    now = state.clock()
    summary = reports.dashboard(conn, state.settings.tz, now)
    return render(
        request,
        "dashboard.html",
        summary=summary,
        chart=hourly_bars(summary["hours"], state.local_now().hour),
        events=reports.list_events(conn, limit=14),
        today=long_date(state.local_now()),
        today_iso=state.local_now().strftime("%Y-%m-%d"),
        active_nav="hoy",
    )


@router.get("/api/eventos/recientes")
def recent_events(
    desde: int = Query(default=0),
    _: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> JSONResponse:
    """Lo consulta el tablero cada pocos segundos para mostrar lo que acaba de pasar."""
    rows = conn.execute(
        """SELECT e.id, e.ts, e.outcome, e.reason, e.method, p.full_name, z.name AS zone_name
           FROM events e LEFT JOIN people p ON p.id = e.person_id
           LEFT JOIN zones z ON z.id = e.zone_id
           WHERE e.id > ? ORDER BY e.id DESC LIMIT 20""",
        (desde,),
    ).fetchall()
    return JSONResponse(
        [
            {
                "id": row["id"],
                "time": reports.to_local(row["ts"], state.settings.tz).strftime("%H:%M:%S"),
                "outcome": row["outcome"],
                "reason": policy.REASONS.get(row["reason"], row["reason"]),
                "method": row["method"],
                "person": row["full_name"],
                "zone": row["zone_name"],
            }
            for row in rows
        ]
    )


# --- Puertas ---------------------------------------------------------------------------------


def _doors_page(
    request: Request, conn: sqlite3.Connection, new_kiosk: dict | None = None
) -> HTMLResponse:
    return render(
        request,
        "doors.html",
        zones=conn.execute(
            """SELECT z.*, (SELECT COUNT(DISTINCT person_id) FROM grants g
                            WHERE g.zone_id = z.id) AS people
               FROM zones z ORDER BY z.name"""
        ).fetchall(),
        kiosks=conn.execute(
            """SELECT k.*, z.name AS zone_name FROM kiosks k
               JOIN zones z ON z.id = k.zone_id ORDER BY k.name"""
        ).fetchall(),
        new_kiosk=new_kiosk,
        active_nav="puertas",
    )


@router.get("/puertas", response_class=HTMLResponse)
def doors(
    request: Request,
    _: Admin = Depends(current_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    return _doors_page(request, conn)


@router.post("/puertas/zonas")
def zone_create(
    name: str = Form(..., min_length=2, max_length=80),
    description: str = Form(default="", max_length=200),
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    try:
        conn.execute(
            "INSERT INTO zones (name, description) VALUES (?, ?)",
            (name.strip(), description.strip()),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "Ya existe una zona con ese nombre.") from error
    ledger.record_audit(conn, state.keys.chain_key, admin.username, "zone.create", name.strip())
    return RedirectResponse("/puertas?m=zone_saved", status_code=303)


@router.post("/puertas/zonas/{zone_id}/borrar")
def zone_delete(
    zone_id: int,
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    if conn.execute("SELECT 1 FROM kiosks WHERE zone_id = ?", (zone_id,)).fetchone():
        return RedirectResponse("/puertas?m=zone_in_use", status_code=303)
    conn.execute("DELETE FROM zones WHERE id = ?", (zone_id,))
    ledger.record_audit(conn, state.keys.chain_key, admin.username, "zone.delete", str(zone_id))
    return RedirectResponse("/puertas?m=zone_deleted", status_code=303)


def _valid_webhook(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme in {"http", "https"} and bool(parts.hostname)


@router.post("/puertas/kioscos", response_class=HTMLResponse)
def kiosk_create(
    request: Request,
    name: str = Form(..., min_length=2, max_length=80),
    zone_id: int = Form(...),
    door_webhook_url: str = Form(default="", max_length=300),
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    url = door_webhook_url.strip()
    if url and not _valid_webhook(url):
        raise HTTPException(422, "La URL de la puerta debe empezar por http:// o https://")
    if not conn.execute("SELECT 1 FROM zones WHERE id = ?", (zone_id,)).fetchone():
        raise HTTPException(422, "Esa zona no existe.")
    token = crypto.new_token()
    try:
        cursor = conn.execute(
            "INSERT INTO kiosks (name, zone_id, token_hash, door_webhook_url) VALUES (?, ?, ?, ?)",
            (name.strip(), zone_id, crypto.token_hash(token), url or None),
        )
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "Ya existe un kiosco con ese nombre.") from error
    kiosk_id = int(cursor.lastrowid or 0)
    door_secret = None
    if url:
        door_secret = secrets.token_urlsafe(32)
        conn.execute(
            "UPDATE kiosks SET door_secret = ? WHERE id = ?",
            (state.keys.encrypt(door_secret.encode(), access.door_context(kiosk_id)), kiosk_id),
        )
    ledger.record_audit(conn, state.keys.chain_key, admin.username, "kiosk.create", name.strip())
    # El token va en el fragmento (#): el navegador no lo envía al servidor ni lo deja en registros.
    return _doors_page(
        request,
        conn,
        {
            "name": name.strip(),
            "link": f"{request.base_url}kiosco#token={token}",
            "door_secret": door_secret,
        },
    )


@router.post("/puertas/kioscos/{kiosk_id}/opciones")
def kiosk_options(
    kiosk_id: int,
    liveness_required: str = Form(default=""),
    allow_pin: str = Form(default=""),
    active: str = Form(default=""),
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    conn.execute(
        "UPDATE kiosks SET liveness_required = ?, allow_pin = ?, active = ? WHERE id = ?",
        (1 if liveness_required else 0, 1 if allow_pin else 0, 1 if active else 0, kiosk_id),
    )
    ledger.record_audit(
        conn,
        state.keys.chain_key,
        admin.username,
        "kiosk.update",
        str(kiosk_id),
        f"presencia={bool(liveness_required)} pin={bool(allow_pin)} activo={bool(active)}",
    )
    return RedirectResponse("/puertas?m=kiosk_saved", status_code=303)


@router.post("/puertas/kioscos/{kiosk_id}/borrar")
def kiosk_delete(
    kiosk_id: int,
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    conn.execute("DELETE FROM kiosks WHERE id = ?", (kiosk_id,))
    ledger.record_audit(conn, state.keys.chain_key, admin.username, "kiosk.delete", str(kiosk_id))
    return RedirectResponse("/puertas?m=kiosk_deleted", status_code=303)


# --- Eventos y asistencia ---------------------------------------------------------------------


def _event_filters(state: AppState, desde: str, hasta: str) -> tuple[date, date, str, str]:
    today = state.local_now().date()
    start_day = _day(desde, today - timedelta(days=7))
    end_day = _day(hasta, today)
    start, _ = reports.day_bounds(start_day, state.settings.tz)
    _, end = reports.day_bounds(end_day, state.settings.tz)
    return start_day, end_day, start, end


@router.get("/eventos", response_class=HTMLResponse)
def events_page(
    request: Request,
    desde: str = "",
    hasta: str = "",
    resultado: str = "",
    q: str = "",
    _: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    start_day, end_day, start, end = _event_filters(state, desde, hasta)
    return render(
        request,
        "events.html",
        events=reports.list_events(
            conn, start=start, end=end, outcome=resultado or None, search=q or None, limit=300
        ),
        desde=start_day.isoformat(),
        hasta=end_day.isoformat(),
        resultado=resultado,
        q=q,
        active_nav="eventos",
    )


@router.get("/eventos.csv")
def events_csv(
    desde: str = "",
    hasta: str = "",
    resultado: str = "",
    q: str = "",
    admin: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    _, _, start, end = _event_filters(state, desde, hasta)
    rows = reports.list_events(
        conn, start=start, end=end, outcome=resultado or None, search=q or None, limit=100_000
    )
    tz = state.settings.tz
    ledger.record_audit(
        conn, state.keys.chain_key, admin.username, "events.export", details=f"{len(rows)} filas"
    )
    content = reports.to_csv(
        ["Fecha y hora", "Persona", "Zona", "Kiosco", "Método", "Resultado", "Motivo", "Puerta"],
        (
            [
                reports.to_local(row["ts"], tz).strftime("%Y-%m-%d %H:%M:%S"),
                row["full_name"] or (f"#{row['person_id']}" if row["person_id"] else "Desconocido"),
                row["zone_name"],
                row["kiosk_name"],
                "Rostro" if row["method"] == "face" else "PIN",
                "Concedido" if row["outcome"] == "granted" else "Denegado",
                policy.REASONS.get(row["reason"], row["reason"]),
                row["door_status"],
            ]
            for row in rows
        ),
    )
    return Response(
        content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="eventos.csv"'},
    )


@router.get("/eventos/{event_id}/foto")
def event_photo(
    event_id: int,
    admin: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    if admin.role != "admin":
        raise HTTPException(403, "Tu cuenta es de solo lectura.")
    row = conn.execute("SELECT photo_file FROM events WHERE id = ?", (event_id,)).fetchone()
    if row is None or not row["photo_file"] or not _PHOTO_NAME.match(row["photo_file"]):
        raise HTTPException(404, "Sin foto")
    path = state.settings.photos_dir / row["photo_file"]
    if not path.exists():
        raise HTTPException(404, "Sin foto")
    ledger.record_audit(conn, state.keys.chain_key, admin.username, "photo.view", str(event_id))
    return Response(
        state.keys.decrypt(path.read_bytes(), f"photo:{row['photo_file']}"),
        media_type="image/jpeg",
    )


def _attendance_query(state: AppState, desde: str, hasta: str) -> tuple[date, date]:
    today = state.local_now().date()
    return _day(desde, today - timedelta(days=6)), _day(hasta, today)


@router.get("/asistencia", response_class=HTMLResponse)
def attendance_page(
    request: Request,
    desde: str = "",
    hasta: str = "",
    grupo: str = "",
    _: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    start, end = _attendance_query(state, desde, hasta)
    groups = [
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT group_name FROM people WHERE group_name <> '' ORDER BY 1"
        )
    ]
    return render(
        request,
        "attendance.html",
        rows=reports.attendance(conn, state.settings.tz, start, end, grupo or None),
        desde=start.isoformat(),
        hasta=end.isoformat(),
        grupo=grupo,
        groups=groups,
        active_nav="asistencia",
    )


@router.get("/asistencia.csv")
def attendance_csv(
    desde: str = "",
    hasta: str = "",
    grupo: str = "",
    admin: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    start, end = _attendance_query(state, desde, hasta)
    rows = reports.attendance(conn, state.settings.tz, start, end, grupo or None)
    ledger.record_audit(
        conn,
        state.keys.chain_key,
        admin.username,
        "attendance.export",
        details=f"{len(rows)} filas",
    )
    content = reports.to_csv(
        ["Fecha", "Persona", "Grupo", "Primera marca", "Última marca", "Horas", "Marcas"],
        (
            [
                entry["day"].isoformat(),
                entry["name"],
                entry["group"],
                entry["first"].strftime("%H:%M"),
                entry["last"].strftime("%H:%M"),
                str(entry["hours"]).replace(".", ","),
                entry["marks"],
            ]
            for entry in rows
        ),
    )
    return Response(
        content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="asistencia.csv"'},
    )


# --- Bitácora y privacidad ---------------------------------------------------------------------


@router.get("/bitacora", response_class=HTMLResponse)
def audit_page(
    request: Request,
    _: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    return render(
        request,
        "audit.html",
        rows=conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 200").fetchall(),
        event_chain=ledger.verify_events(conn, state.keys.chain_key),
        audit_chain=ledger.verify_audit(conn, state.keys.chain_key),
        active_nav="bitacora",
    )


def _privacy_counts(conn: sqlite3.Connection) -> sqlite3.Row:
    return conn.execute(
        """SELECT
             (SELECT COUNT(DISTINCT person_id) FROM templates) AS with_faces,
             (SELECT COUNT(*) FROM people WHERE pin_lookup IS NOT NULL) AS with_pin,
             (SELECT COUNT(*) FROM people) AS total,
             (SELECT COUNT(*) FROM events) AS events,
             (SELECT MIN(ts) FROM events) AS oldest"""
    ).fetchone()


@router.get("/privacidad", response_class=HTMLResponse)
def privacy_page(
    request: Request,
    _: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    return render(
        request,
        "privacy.html",
        counts=_privacy_counts(conn),
        settings=state.settings,
        policy_version=people.POLICY_VERSION,
        purged=None,
        active_nav="privacidad",
    )


@router.post("/privacidad/purgar", response_class=HTMLResponse)
def privacy_purge(
    request: Request,
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    purged = people.purge_expired(
        conn, state.settings, state.keys.chain_key, state.clock(), admin.username
    )
    return render(
        request,
        "privacy.html",
        counts=_privacy_counts(conn),
        settings=state.settings,
        policy_version=people.POLICY_VERSION,
        purged=purged,
        active_nav="privacidad",
    )


@router.get("/cuenta", response_class=HTMLResponse)
def account_page(request: Request, _: Admin = Depends(current_admin)) -> Response:
    return render(request, "account.html", active_nav=None)
