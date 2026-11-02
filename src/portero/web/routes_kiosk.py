"""Pantalla del kiosco y su API. El kiosco se autentica con un token de dispositivo."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from .. import crypto, ledger
from ..biometrics.engine import decode_image
from ..state import AppState
from .deps import app_state, get_db, templates

router = APIRouter()


def current_kiosk(
    authorization: str | None = Header(default=None),
    state: AppState = Depends(app_state),
    conn: sqlite3.Connection = Depends(get_db),
) -> sqlite3.Row:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Kiosco no autorizado")
    kiosk = conn.execute(
        """SELECT k.*, z.name AS zone_name FROM kiosks k JOIN zones z ON z.id = k.zone_id
           WHERE k.token_hash = ? AND k.active = 1""",
        (crypto.token_hash(token),),
    ).fetchone()
    if kiosk is None:
        raise HTTPException(401, "Kiosco no autorizado")
    # Una vez por minuto basta para saber si sigue en línea, y evita desgastar tarjetas SD.
    now = state.clock()
    if not kiosk["last_seen_at"] or kiosk["last_seen_at"] < ledger.iso(now - timedelta(minutes=1)):
        conn.execute(
            "UPDATE kiosks SET last_seen_at = ? WHERE id = ?", (ledger.iso(now), kiosk["id"])
        )
    return kiosk


@router.get("/kiosco", response_class=HTMLResponse)
def kiosk_page(request: Request) -> Response:
    return templates.TemplateResponse(request, "kiosk.html", {})


@router.get("/api/kiosk/v1/config")
def kiosk_config(kiosk: sqlite3.Row = Depends(current_kiosk)) -> dict:
    return {
        "name": kiosk["name"],
        "zone": kiosk["zone_name"],
        "allow_pin": bool(kiosk["allow_pin"]),
        "liveness": bool(kiosk["liveness_required"]),
    }


@router.post("/api/kiosk/v1/frame")
async def kiosk_frame(
    request: Request,
    kiosk: sqlite3.Row = Depends(current_kiosk),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    data = await request.body()
    image = await run_in_threadpool(decode_image, data)
    if image is None:
        raise HTTPException(422, "El cuadro no es una imagen válida")
    return await run_in_threadpool(request.app.state.flow.process_frame, conn, kiosk, image)


class PinBody(BaseModel):
    pin: str = Field(pattern=r"^\d{6}$")


@router.post("/api/kiosk/v1/pin")
def kiosk_pin(
    body: PinBody,
    request: Request,
    kiosk: sqlite3.Row = Depends(current_kiosk),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    if not kiosk["allow_pin"]:
        raise HTTPException(403, "Este kiosco no acepta PIN")
    return request.app.state.flow.submit_pin(conn, kiosk, body.pin)
