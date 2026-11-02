"""Decisión final de acceso, compartida por rostro y PIN."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass

import cv2
import numpy as np

from . import ledger, policy
from .state import AppState


@dataclass(frozen=True)
class Outcome:
    granted: bool
    reason: str
    person_id: int | None
    first_name: str | None
    event_id: int
    door_status: str | None


def first_name(full_name: str) -> str:
    # En pantalla pública solo se muestra el primer nombre.
    return full_name.split()[0] if full_name.strip() else ""


def door_context(kiosk_id: int) -> str:
    return f"door:{kiosk_id}"


def _store_photo(state: AppState, frame: np.ndarray, moment: str) -> str | None:
    """Guarda cifrada la foto de un intento denegado, solo si la organización lo activó."""
    if not state.settings.store_denied_photos:
        return None
    ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not ok:
        return None
    name = f"{moment[:10]}-{uuid.uuid4().hex}.enc"
    directory = state.settings.photos_dir
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(state.keys.encrypt(encoded.tobytes(), f"photo:{name}"))
    return name


def conclude(
    state: AppState,
    conn: sqlite3.Connection,
    kiosk: sqlite3.Row,
    *,
    person_id: int | None,
    method: str,
    denial: str | None = None,
    score: float | None = None,
    frame: np.ndarray | None = None,
) -> Outcome:
    """Evalúa la política, registra el evento y solo después abre la puerta.

    El orden es deliberado: si el registro falla, salta la excepción y la puerta sigue cerrada.
    """
    person = None
    if person_id is not None:
        person = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()

    reason = denial
    if reason is None:
        if person is None:
            reason = "unknown_face"
        else:
            reason = policy.evaluate(
                bool(person["active"]),
                policy.grants_for(conn, person["id"]),
                kiosk["zone_id"],
                state.local_now(),
            )
    granted = reason == "ok"
    if granted and method == "pin":
        reason = "ok_pin"

    now = state.clock()
    photo = None
    if not granted and frame is not None:
        photo = _store_photo(state, frame, ledger.iso(now))

    event_id = ledger.record_event(
        conn,
        state.keys.chain_key,
        kiosk_id=kiosk["id"],
        zone_id=kiosk["zone_id"],
        person_id=person["id"] if person is not None else None,
        method=method,
        outcome="granted" if granted else "denied",
        reason=reason,
        score=score,
        photo_file=photo,
        when=now,
    )

    door_status = None
    if granted and kiosk["door_webhook_url"]:
        secret = state.keys.decrypt(kiosk["door_secret"], door_context(kiosk["id"])).decode()
        door_status = state.door.open(
            kiosk["door_webhook_url"],
            secret,
            {"event": event_id, "kiosk": kiosk["name"], "action": "open"},
        )
        conn.execute("UPDATE events SET door_status = ? WHERE id = ?", (door_status, event_id))

    return Outcome(
        granted=granted,
        reason=reason,
        person_id=person["id"] if person is not None else None,
        first_name=first_name(person["full_name"]) if person is not None else None,
        event_id=event_id,
        door_status=door_status,
    )
