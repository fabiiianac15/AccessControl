"""Inicio y cierre de sesión, cambio de contraseña."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from .. import crypto, ledger
from ..state import AppState
from .deps import SESSION_COOKIE, Admin, app_state, form_member, get_db, render

router = APIRouter()

MAX_FAILURES = 5
LOCK_MINUTES = 10
MIN_PASSWORD = 12


def _login_page(
    request: Request, conn: sqlite3.Connection, error: str | None = None, status: int = 200
) -> HTMLResponse:
    has_admins = conn.execute("SELECT 1 FROM admins LIMIT 1").fetchone() is not None
    return render(request, "login.html", status_code=status, error=error, has_admins=has_admins)


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> Response:
    return _login_page(request, conn)


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    now = state.clock()
    row = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()

    # Se verifica la contraseña aunque la cuenta no exista o esté bloqueada, para que el tiempo
    # de respuesta no revele cuáles existen.
    valid = crypto.verify_password(row["password_hash"] if row else None, password)
    if row and row["locked_until"] and row["locked_until"] > ledger.iso(now):
        return _login_page(request, conn, "Cuenta bloqueada temporalmente. Intenta más tarde.", 429)

    if not row or not valid:
        if row:
            failures = row["failed_logins"] + 1
            locked = (
                ledger.iso(now + timedelta(minutes=LOCK_MINUTES))
                if failures >= MAX_FAILURES
                else None
            )
            conn.execute(
                "UPDATE admins SET failed_logins = ?, locked_until = ? WHERE id = ?",
                (0 if locked else failures, locked, row["id"]),
            )
            if locked:
                ledger.record_audit(
                    conn, state.keys.chain_key, row["username"], "login.locked", row["username"]
                )
        return _login_page(request, conn, "Usuario o contraseña incorrectos.", 401)

    token = crypto.new_token()
    conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (ledger.iso(now),))
    conn.execute(
        "UPDATE admins SET failed_logins = 0, locked_until = NULL WHERE id = ?", (row["id"],)
    )
    conn.execute(
        "INSERT INTO sessions (token_hash, admin_id, csrf_token, expires_at) VALUES (?, ?, ?, ?)",
        (
            crypto.token_hash(token),
            row["id"],
            crypto.new_token(),
            ledger.iso(now + timedelta(hours=state.settings.session_hours)),
        ),
    )
    ledger.record_audit(conn, state.keys.chain_key, row["username"], "login", row["username"])

    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=state.settings.session_hours * 3600,
        path="/",
    )
    return response


@router.post("/logout")
def logout(
    request: Request,
    admin: Admin = Depends(form_member),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    token = request.cookies.get(SESSION_COOKIE, "")
    conn.execute("DELETE FROM sessions WHERE token_hash = ?", (crypto.token_hash(token),))
    ledger.record_audit(conn, state.keys.chain_key, admin.username, "logout", admin.username)
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.post("/cuenta/contrasena")
def change_password(
    current: str = Form(...),
    new: str = Form(...),
    admin: Admin = Depends(form_member),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    row = conn.execute("SELECT password_hash FROM admins WHERE id = ?", (admin.id,)).fetchone()
    if len(new) < MIN_PASSWORD or not crypto.verify_password(row["password_hash"], current):
        return RedirectResponse("/cuenta?m=password_bad", status_code=303)
    conn.execute(
        "UPDATE admins SET password_hash = ? WHERE id = ?", (crypto.hash_password(new), admin.id)
    )
    # Cierra las demás sesiones: si alguien robó una, deja de servirle.
    conn.execute("DELETE FROM sessions WHERE admin_id = ?", (admin.id,))
    ledger.record_audit(
        conn, state.keys.chain_key, admin.username, "password.change", admin.username
    )
    return RedirectResponse("/login", status_code=303)
