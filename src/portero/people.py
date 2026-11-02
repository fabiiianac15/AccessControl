"""Personas: registro facial, autorizaciones, PIN, exportación y supresión."""

from __future__ import annotations

import base64
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np

from . import crypto, ledger
from .biometrics import quality
from .biometrics.engine import MODEL_NAME
from .biometrics.gallery import pack_template, template_context
from .biometrics.liveness import face_aspect
from .config import Settings
from .db import tx
from .state import AppState

# Cambia esta versión al modificar el texto de templates/print_consent.html: cada autorización
# queda ligada a la versión que la persona firmó.
POLICY_VERSION = "2026-11"

ENROLL_MESSAGES = {
    "no_face": "No se ve ningún rostro",
    "many_faces": "Debe aparecer una sola persona",
    "duplicate": "Este rostro ya está registrado con otra persona",
    "other_person": "Este rostro no coincide con las muestras anteriores",
    "no_consent": "Registra primero la autorización de la persona",
    "full": "Ya se alcanzó el máximo de muestras",
    "accepted": "Muestra guardada",
    **quality.HINTS,
}
SAME_PERSON_MIN = 0.45


def active_consent(conn: sqlite3.Connection, person_id: int) -> sqlite3.Row | None:
    return conn.execute(
        """SELECT * FROM consents WHERE person_id = ? AND revoked_at IS NULL
           ORDER BY id DESC LIMIT 1""",
        (person_id,),
    ).fetchone()


def template_count(conn: sqlite3.Connection, person_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM templates WHERE person_id = ?", (person_id,)
    ).fetchone()[0]


@dataclass(frozen=True)
class EnrollResult:
    accepted: bool
    code: str
    samples: int
    box: list[float] | None = None

    @property
    def message(self) -> str:
        return ENROLL_MESSAGES[self.code]


def add_sample(
    state: AppState, conn: sqlite3.Connection, person_id: int, image: np.ndarray
) -> EnrollResult:
    """Valida una muestra y la guarda cifrada. La autorización se exige aquí, no en la interfaz."""
    settings = state.settings
    count = template_count(conn, person_id)
    if active_consent(conn, person_id) is None:
        return EnrollResult(False, "no_consent", count)
    if count >= settings.max_samples:
        return EnrollResult(False, "full", count)

    faces = state.engine.detect(image)
    if not faces:
        return EnrollResult(False, "no_face", count)
    height, width = image.shape[:2]
    x, y, w, h = faces[0].box
    box = [round(x / width, 4), round(y / height, 4), round(w / width, 4), round(h / height, 4)]
    if len(faces) > 1:
        return EnrollResult(False, "many_faces", count, box)

    check = quality.assess(image, faces[0])
    if not check.ok:
        return EnrollResult(False, check.issue or "no_face", count, box)

    embedding = state.engine.embed(image, faces[0])

    # Evita dos identidades para un mismo rostro: compararlas sería siempre ambiguo.
    _, other_score = state.gallery.best(embedding, exclude=person_id)
    if other_score >= settings.match_threshold:
        return EnrollResult(False, "duplicate", count, box)
    # -1 significa que la galería aún no tiene sus muestras (persona inactiva, por ejemplo).
    own_score = state.gallery.score_for(embedding, person_id)
    if count and -1 < own_score < SAME_PERSON_MIN:
        return EnrollResult(False, "other_person", count, box)

    blob = state.keys.encrypt(
        pack_template(embedding, face_aspect(faces[0].landmarks)), template_context(person_id)
    )
    conn.execute(
        """INSERT INTO templates (person_id, ciphertext, quality, model, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (person_id, blob, check.score, MODEL_NAME, ledger.iso(state.clock())),
    )
    state.gallery.reload(conn, state.keys)
    return EnrollResult(True, "accepted", count + 1, box)


def assign_pin(state: AppState, conn: sqlite3.Connection, person_id: int) -> str:
    """Genera un PIN único. Solo se muestra una vez: en la base queda su HMAC."""
    for _ in range(50):
        pin = crypto.new_pin()
        try:
            conn.execute(
                "UPDATE people SET pin_lookup = ? WHERE id = ?",
                (state.keys.pin_lookup(pin), person_id),
            )
        except sqlite3.IntegrityError:
            continue
        return pin
    raise RuntimeError("No se pudo generar un PIN único")


def revoke_consent(state: AppState, conn: sqlite3.Connection, person_id: int, actor: str) -> int:
    """Retira la autorización y borra de inmediato las plantillas. La persona conserva su PIN."""
    with tx(conn):
        conn.execute(
            """UPDATE consents SET revoked_at = ?, revoked_by = ?
               WHERE person_id = ? AND revoked_at IS NULL""",
            (ledger.iso(state.clock()), actor, person_id),
        )
        deleted = conn.execute("DELETE FROM templates WHERE person_id = ?", (person_id,)).rowcount
        ledger.record_audit(
            conn,
            state.keys.chain_key,
            actor,
            "consent.revoke",
            f"persona:{person_id}",
            f"{deleted} plantillas borradas",
        )
    state.gallery.reload(conn, state.keys)
    return deleted


def erase_person(state: AppState, conn: sqlite3.Connection, person_id: int, actor: str) -> None:
    """Supresión total. Los eventos quedan como seudónimo numérico y la cadena sigue válida."""
    photos = [
        row["photo_file"]
        for row in conn.execute(
            "SELECT photo_file FROM events WHERE person_id = ? AND photo_file IS NOT NULL",
            (person_id,),
        )
    ]
    with tx(conn):
        conn.execute("UPDATE events SET photo_file = NULL WHERE person_id = ?", (person_id,))
        conn.execute("DELETE FROM people WHERE id = ?", (person_id,))
        ledger.record_audit(
            conn, state.keys.chain_key, actor, "person.erase", f"persona:{person_id}"
        )
    for name in photos:
        (state.settings.photos_dir / name).unlink(missing_ok=True)
    state.gallery.reload(conn, state.keys)


def export_person(state: AppState, conn: sqlite3.Connection, person_id: int) -> dict:
    """Todo lo que el sistema guarda sobre una persona, para atender una consulta del titular."""
    person = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
    if person is None:
        raise LookupError(person_id)
    templates = conn.execute(
        "SELECT id, ciphertext, quality, model, created_at FROM templates WHERE person_id = ?",
        (person_id,),
    ).fetchall()
    return {
        "persona": {
            "id": person["id"],
            "nombre": person["full_name"],
            "documento": person["document"],
            "grupo": person["group_name"],
            "activa": bool(person["active"]),
            "tiene_pin": person["pin_lookup"] is not None,
            "creada": person["created_at"],
        },
        "autorizaciones": [
            dict(row)
            for row in conn.execute("SELECT * FROM consents WHERE person_id = ?", (person_id,))
        ],
        "plantillas_faciales": [
            {
                "id": row["id"],
                "modelo": row["model"],
                "calidad": row["quality"],
                "creada": row["created_at"],
                "vector_base64": base64.b64encode(
                    state.keys.decrypt(row["ciphertext"], template_context(person_id))
                ).decode(),
            }
            for row in templates
        ],
        "permisos": [
            dict(row)
            for row in conn.execute("SELECT * FROM grants WHERE person_id = ?", (person_id,))
        ],
        "eventos": [
            dict(row)
            for row in conn.execute(
                """SELECT ts, zone_id, kiosk_id, method, outcome, reason, score, door_status
                   FROM events WHERE person_id = ? ORDER BY id""",
                (person_id,),
            )
        ],
    }


def purge_expired(
    conn: sqlite3.Connection,
    settings: Settings,
    chain_key: bytes,
    now: datetime,
    actor: str = "sistema",
) -> dict:
    """Aplica la retención a eventos y fotos antiguas, dejando constancia en la bitácora."""
    cutoff = ledger.iso(now - timedelta(days=settings.retention_days))
    photos = [
        row["photo_file"]
        for row in conn.execute(
            "SELECT photo_file FROM events WHERE ts < ? AND photo_file IS NOT NULL", (cutoff,)
        )
    ]
    with tx(conn):
        last = conn.execute(
            "SELECT id, hash FROM events WHERE ts < ? ORDER BY id DESC LIMIT 1", (cutoff,)
        ).fetchone()
        deleted = conn.execute("DELETE FROM events WHERE ts < ?", (cutoff,)).rowcount
        if deleted:
            # Ancla: permite comprobar luego que el borrado partió de este punto de la cadena.
            ledger.record_audit(
                conn,
                chain_key,
                actor,
                "retention.purge",
                f"eventos hasta #{last['id']}",
                f"{deleted} eventos; último hash {last['hash']}",
            )
    for name in photos:
        (settings.photos_dir / name).unlink(missing_ok=True)
    return {"events": deleted, "photos": len(photos), "cutoff": cutoff}
