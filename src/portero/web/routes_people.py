"""Personas: datos, autorización, muestras faciales, PIN, permisos y derechos del titular."""

from __future__ import annotations

import json
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from .. import ledger, people, reports
from ..biometrics.engine import decode_image
from ..policy import ALL_WEEK, WEEKDAYS_ES
from ..state import AppState
from .deps import Admin, api_writer, app_state, current_admin, form_writer, get_db, render

router = APIRouter()


def _person_or_404(conn: sqlite3.Connection, person_id: int) -> sqlite3.Row:
    person = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
    if person is None:
        raise HTTPException(404, "Persona no encontrada")
    return person


def _to(person_id: int, notice: str) -> RedirectResponse:
    return RedirectResponse(f"/personas/{person_id}?m={notice}", status_code=303)


def _audit(
    state: AppState,
    conn: sqlite3.Connection,
    admin: Admin,
    action: str,
    person_id: int,
    details: str = "",
) -> None:
    ledger.record_audit(
        conn, state.keys.chain_key, admin.username, action, f"persona:{person_id}", details
    )


@router.get("/personas", response_class=HTMLResponse)
def people_list(
    request: Request,
    q: str = Query(default=""),
    grupo: str = Query(default=""),
    _: Admin = Depends(current_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    where, params = [], []
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where.append("(p.full_name LIKE ? ESCAPE '\\' OR p.document LIKE ? ESCAPE '\\')")
        params += [f"%{escaped}%", f"%{escaped}%"]
    if grupo:
        where.append("p.group_name = ?")
        params.append(grupo)
    condition = f"WHERE {' AND '.join(where)}" if where else ""
    rows = conn.execute(
        f"""SELECT p.*,
              (SELECT COUNT(*) FROM templates t WHERE t.person_id = p.id) AS samples,
              EXISTS (SELECT 1 FROM consents c
                      WHERE c.person_id = p.id AND c.revoked_at IS NULL) AS has_consent,
              (SELECT MAX(ts) FROM events e
               WHERE e.person_id = p.id AND e.outcome = 'granted') AS last_access
            FROM people p {condition} ORDER BY p.full_name LIMIT 500""",
        params,
    ).fetchall()
    groups = [
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT group_name FROM people WHERE group_name <> '' ORDER BY 1"
        )
    ]
    return render(
        request,
        "people_list.html",
        people=rows,
        groups=groups,
        q=q,
        grupo=grupo,
        active_nav="personas",
    )


@router.get("/personas/nueva", response_class=HTMLResponse)
def person_new(request: Request, _: Admin = Depends(current_admin)) -> Response:
    return render(request, "person_form.html", person=None, active_nav="personas")


@router.post("/personas/nueva")
def person_create(
    full_name: str = Form(..., min_length=2, max_length=120),
    document: str = Form(default="", max_length=40),
    group_name: str = Form(default="", max_length=60),
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    cursor = conn.execute(
        "INSERT INTO people (full_name, document, group_name, created_at) VALUES (?, ?, ?, ?)",
        (
            full_name.strip(),
            document.strip() or None,
            group_name.strip(),
            ledger.iso(state.clock()),
        ),
    )
    person_id = int(cursor.lastrowid or 0)
    _audit(state, conn, admin, "person.create", person_id)
    return _to(person_id, "person_saved")


@router.get("/personas/{person_id}", response_class=HTMLResponse)
def person_detail(
    request: Request,
    person_id: int,
    _: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    person = _person_or_404(conn, person_id)
    grants = conn.execute(
        """SELECT g.*, z.name AS zone_name FROM grants g JOIN zones z ON z.id = g.zone_id
           WHERE g.person_id = ? ORDER BY z.name""",
        (person_id,),
    ).fetchall()
    return render(
        request,
        "person_detail.html",
        person=person,
        consent=people.active_consent(conn, person_id),
        consents=conn.execute(
            "SELECT * FROM consents WHERE person_id = ? ORDER BY id DESC", (person_id,)
        ).fetchall(),
        samples=people.template_count(conn, person_id),
        min_samples=state.settings.min_samples,
        grants=grants,
        zones=conn.execute("SELECT * FROM zones ORDER BY name").fetchall(),
        events=reports.list_events(conn, person_id=person_id, limit=15),
        weekdays=WEEKDAYS_ES,
        policy_version=people.POLICY_VERSION,
        new_pin=None,
        active_nav="personas",
    )


@router.post("/personas/{person_id}/editar")
def person_update(
    person_id: int,
    full_name: str = Form(..., min_length=2, max_length=120),
    document: str = Form(default="", max_length=40),
    group_name: str = Form(default="", max_length=60),
    active: str = Form(default=""),
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    _person_or_404(conn, person_id)
    conn.execute(
        "UPDATE people SET full_name = ?, document = ?, group_name = ?, active = ? WHERE id = ?",
        (
            full_name.strip(),
            document.strip() or None,
            group_name.strip(),
            1 if active else 0,
            person_id,
        ),
    )
    _audit(state, conn, admin, "person.update", person_id, f"activa={bool(active)}")
    state.gallery.reload(conn, state.keys)
    return _to(person_id, "person_saved")


@router.post("/personas/{person_id}/autorizacion")
def consent_record(
    person_id: int,
    evidence: str = Form(..., min_length=3, max_length=200),
    confirmed: str = Form(...),
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    _person_or_404(conn, person_id)
    if people.active_consent(conn, person_id) is None:
        conn.execute(
            """INSERT INTO consents (person_id, policy_version, evidence, granted_at, recorded_by)
               VALUES (?, ?, ?, ?, ?)""",
            (
                person_id,
                people.POLICY_VERSION,
                evidence.strip(),
                ledger.iso(state.clock()),
                admin.username,
            ),
        )
        _audit(state, conn, admin, "consent.grant", person_id, people.POLICY_VERSION)
    state.gallery.reload(conn, state.keys)
    return _to(person_id, "consent_saved")


@router.post("/personas/{person_id}/autorizacion/retirar")
def consent_revoke(
    person_id: int,
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    _person_or_404(conn, person_id)
    people.revoke_consent(state, conn, person_id, admin.username)
    return _to(person_id, "consent_revoked")


@router.get("/personas/{person_id}/autorizacion/imprimir", response_class=HTMLResponse)
def consent_print(
    request: Request,
    person_id: int,
    _: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    return render(
        request,
        "print_consent.html",
        person=_person_or_404(conn, person_id),
        policy_version=people.POLICY_VERSION,
        privacy_contact=state.settings.privacy_contact,
        today=state.local_now().strftime("%d/%m/%Y"),
    )


@router.get("/personas/{person_id}/rostro", response_class=HTMLResponse)
def enroll_page(
    request: Request,
    person_id: int,
    admin: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    if admin.role != "admin":
        raise HTTPException(403, "Tu cuenta es de solo lectura.")
    person = _person_or_404(conn, person_id)
    if people.active_consent(conn, person_id) is None:
        return RedirectResponse(f"/personas/{person_id}", status_code=303)
    return render(
        request,
        "enroll.html",
        person=person,
        samples=people.template_count(conn, person_id),
        min_samples=state.settings.min_samples,
        max_samples=state.settings.max_samples,
        active_nav="personas",
    )


@router.post("/api/personas/{person_id}/muestras")
async def enroll_sample(
    request: Request,
    person_id: int,
    admin: Admin = Depends(api_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    _person_or_404(conn, person_id)
    image = await run_in_threadpool(decode_image, await request.body())
    if image is None:
        raise HTTPException(422, "El archivo no es una imagen válida")
    result = await run_in_threadpool(people.add_sample, state, conn, person_id, image)
    if result.accepted:
        _audit(state, conn, admin, "template.add", person_id, f"muestra {result.samples}")
    return {
        "accepted": result.accepted,
        "code": result.code,
        "message": result.message,
        "samples": result.samples,
        "box": result.box,
    }


@router.post("/personas/{person_id}/rostro/borrar")
def faces_delete(
    person_id: int,
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    _person_or_404(conn, person_id)
    deleted = conn.execute("DELETE FROM templates WHERE person_id = ?", (person_id,)).rowcount
    _audit(state, conn, admin, "template.delete", person_id, f"{deleted} plantillas")
    state.gallery.reload(conn, state.keys)
    return _to(person_id, "faces_deleted")


@router.post("/personas/{person_id}/pin", response_class=HTMLResponse)
def pin_generate(
    request: Request,
    person_id: int,
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    person = _person_or_404(conn, person_id)
    pin = people.assign_pin(state, conn, person_id)
    _audit(state, conn, admin, "pin.assign", person_id)
    # Se muestra en la respuesta del POST y nunca más: no hay forma de recuperarlo después.
    return render(request, "pin_once.html", person=person, pin=pin, active_nav="personas")


@router.post("/personas/{person_id}/pin/quitar")
def pin_remove(
    person_id: int,
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    _person_or_404(conn, person_id)
    conn.execute("UPDATE people SET pin_lookup = NULL WHERE id = ?", (person_id,))
    _audit(state, conn, admin, "pin.remove", person_id)
    return _to(person_id, "pin_removed")


def _minutes(value: str) -> int | None:
    try:
        hours, minutes = value.split(":")
        total = int(hours) * 60 + int(minutes)
    except ValueError:
        return None
    return total if 0 <= total <= 1440 else None


def _parse_day(value: str) -> str | None:
    return date.fromisoformat(value).isoformat() if value else None


@router.post("/personas/{person_id}/permisos")
async def grant_create(
    request: Request,
    person_id: int,
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    _person_or_404(conn, person_id)
    form = await request.form()
    days = {str(day) for day in form.getlist("days")}
    mask = sum(1 << bit for bit in range(7) if str(bit) in days)
    start = _minutes(str(form.get("start", "00:00")))
    # 00:00 como fin significa fin del día, no un turno de cero minutos.
    raw_end = str(form.get("end", "23:59"))
    end = 1440 if raw_end == "00:00" else _minutes(raw_end)
    try:
        zone_id = int(str(form.get("zone_id", "")))
        valid_from = _parse_day(str(form.get("valid_from", "")))
        valid_until = _parse_day(str(form.get("valid_until", "")))
    except ValueError:
        return _to(person_id, "grant_bad")
    zone_exists = conn.execute("SELECT 1 FROM zones WHERE id = ?", (zone_id,)).fetchone()
    invalid_range = valid_from and valid_until and valid_from > valid_until
    if not zone_exists or not mask or start is None or end is None or start == end or invalid_range:
        return _to(person_id, "grant_bad")
    conn.execute(
        """INSERT INTO grants (person_id, zone_id, weekdays, start_minute, end_minute,
                               valid_from, valid_until)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (person_id, zone_id, mask & ALL_WEEK, start, end, valid_from, valid_until),
    )
    _audit(state, conn, admin, "grant.create", person_id, f"zona {zone_id}")
    return _to(person_id, "grant_saved")


@router.post("/personas/{person_id}/permisos/{grant_id}/quitar")
def grant_delete(
    person_id: int,
    grant_id: int,
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    conn.execute("DELETE FROM grants WHERE id = ? AND person_id = ?", (grant_id, person_id))
    _audit(state, conn, admin, "grant.delete", person_id, f"permiso {grant_id}")
    return _to(person_id, "grant_deleted")


@router.get("/personas/{person_id}/exportar")
def person_export(
    person_id: int,
    admin: Admin = Depends(current_admin),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    if admin.role != "admin":
        raise HTTPException(403, "Tu cuenta es de solo lectura.")
    _person_or_404(conn, person_id)
    data = people.export_person(state, conn, person_id)
    _audit(state, conn, admin, "person.export", person_id)
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="persona-{person_id}.json"'},
    )


@router.post("/personas/{person_id}/suprimir")
def person_erase(
    person_id: int,
    confirm: str = Form(default=""),
    admin: Admin = Depends(form_writer),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    person = _person_or_404(conn, person_id)
    if confirm.strip() != person["full_name"]:
        raise HTTPException(422, "Escribe el nombre exacto para confirmar la supresión.")
    people.erase_person(state, conn, person_id, admin.username)
    return RedirectResponse("/personas?m=person_erased", status_code=303)
