"""Registros encadenados con HMAC: eventos de acceso y bitácora de administración.

Cada fila firma su contenido junto con la firma anterior. Sin la clave, alterar, borrar o insertar
una fila intermedia deja la cadena rota y `verify_*` señala el punto exacto.

Las firmas no cubren nombres. Por eso suprimir a una persona no rompe la cadena.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from .db import tx

GENESIS = "0" * 64
_EVENT_FIELDS = ("ts", "kiosk_id", "zone_id", "person_id", "method", "outcome", "reason", "score")
_AUDIT_FIELDS = ("ts", "actor", "action", "subject", "details")


def utcnow() -> datetime:
    return datetime.now(UTC)


def iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="milliseconds")


def _sign(key: bytes, prev_hash: str, fields: dict[str, object]) -> str:
    payload = json.dumps(fields, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hmac.new(key, f"{prev_hash}|{payload}".encode(), hashlib.sha256).hexdigest()


def _last_hash(conn: sqlite3.Connection, table: str) -> str:
    row = conn.execute(f"SELECT hash FROM {table} ORDER BY id DESC LIMIT 1").fetchone()
    return row["hash"] if row else GENESIS


def record_event(
    conn: sqlite3.Connection,
    key: bytes,
    *,
    kiosk_id: int | None,
    zone_id: int | None,
    person_id: int | None,
    method: str,
    outcome: str,
    reason: str,
    score: float | None = None,
    photo_file: str | None = None,
    when: datetime | None = None,
) -> int:
    fields: dict[str, object] = {
        "ts": iso(when or utcnow()),
        "kiosk_id": kiosk_id,
        "zone_id": zone_id,
        "person_id": person_id,
        "method": method,
        "outcome": outcome,
        "reason": reason,
        "score": None if score is None else round(float(score), 4),
    }
    with tx(conn):
        prev = _last_hash(conn, "events")
        cursor = conn.execute(
            """INSERT INTO events (ts, kiosk_id, zone_id, person_id, method, outcome, reason,
                                   score, photo_file, prev_hash, hash)
               VALUES (:ts, :kiosk_id, :zone_id, :person_id, :method, :outcome, :reason,
                       :score, :photo_file, :prev_hash, :hash)""",
            {
                **fields,
                "photo_file": photo_file,
                "prev_hash": prev,
                "hash": _sign(key, prev, fields),
            },
        )
    return int(cursor.lastrowid or 0)


def record_audit(
    conn: sqlite3.Connection,
    key: bytes,
    actor: str,
    action: str,
    subject: str = "",
    details: str = "",
    when: datetime | None = None,
) -> None:
    fields: dict[str, object] = {
        "ts": iso(when or utcnow()),
        "actor": actor,
        "action": action,
        "subject": subject,
        "details": details,
    }
    with tx(conn):
        prev = _last_hash(conn, "audit_log")
        conn.execute(
            """INSERT INTO audit_log (ts, actor, action, subject, details, prev_hash, hash)
               VALUES (:ts, :actor, :action, :subject, :details, :prev_hash, :hash)""",
            {**fields, "prev_hash": prev, "hash": _sign(key, prev, fields)},
        )


@dataclass(frozen=True)
class ChainReport:
    table: str
    rows: int
    ok: bool
    broken_id: int | None = None
    detail: str = ""


def _verify(
    conn: sqlite3.Connection, key: bytes, table: str, names: tuple[str, ...]
) -> ChainReport:
    rows = 0
    prev: str | None = None
    # La retención elimina las filas más antiguas: la primera que quede fija el punto de partida.
    for row in conn.execute(f"SELECT * FROM {table} ORDER BY id"):
        if prev is not None and row["prev_hash"] != prev:
            return ChainReport(table, rows, False, row["id"], "Falta una fila o se reordenó")
        fields = {name: row[name] for name in names}
        if not hmac.compare_digest(_sign(key, row["prev_hash"], fields), row["hash"]):
            return ChainReport(
                table, rows, False, row["id"], "El contenido no coincide con la firma"
            )
        prev = row["hash"]
        rows += 1
    return ChainReport(table, rows, True)


def verify_events(conn: sqlite3.Connection, key: bytes) -> ChainReport:
    return _verify(conn, key, "events", _EVENT_FIELDS)


def verify_audit(conn: sqlite3.Connection, key: bytes) -> ChainReport:
    return _verify(conn, key, "audit_log", _AUDIT_FIELDS)
