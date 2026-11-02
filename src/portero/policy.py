"""Decide si una persona ya identificada puede entrar. Lógica pura, sin base de datos."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

ALL_WEEK = 0b1111111
WEEKDAYS_ES = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")

REASONS = {
    "ok": "Acceso autorizado",
    "ok_pin": "Acceso autorizado con PIN",
    "unknown_face": "Rostro no reconocido",
    "liveness_failed": "No superó la prueba de presencia",
    "identity_changed": "El rostro cambió durante la prueba",
    "inactive": "Persona inactiva",
    "no_grant": "Sin permiso para esta zona",
    "outside_schedule": "Fuera del horario autorizado",
    "not_started": "Permiso aún no vigente",
    "expired": "Permiso vencido",
    "pin_invalid": "PIN incorrecto",
    "pin_locked": "Kiosco bloqueado por intentos de PIN",
}


@dataclass(frozen=True)
class Grant:
    zone_id: int
    weekdays: int = ALL_WEEK
    start_minute: int = 0
    end_minute: int = 1440
    valid_from: date | None = None
    valid_until: date | None = None

    def _in_window(self, moment: datetime) -> bool:
        minute = moment.hour * 60 + moment.minute
        day = moment.weekday()
        if self.start_minute <= self.end_minute:
            return self.start_minute <= minute < self.end_minute and bool(self.weekdays >> day & 1)
        # Turno nocturno (22:00 a 06:00): la madrugada pertenece al día en que empezó el turno.
        if minute >= self.start_minute:
            return bool(self.weekdays >> day & 1)
        if minute < self.end_minute:
            return bool(self.weekdays >> ((day - 1) % 7) & 1)
        return False


def evaluate(active: bool, grants: Iterable[Grant], zone_id: int, now: datetime) -> str:
    """Devuelve 'ok' o el motivo de denegación. `now` va en hora local de la organización."""
    if not active:
        return "inactive"
    relevant = [g for g in grants if g.zone_id == zone_id]
    if not relevant:
        return "no_grant"
    # Con varios permisos basta uno válido; si ninguno sirve, informa el motivo más útil.
    today = now.date()
    reason = "expired"
    for grant in relevant:
        # Un turno nocturno vigente hasta ayer aún cubre la madrugada de hoy.
        overnight_tail = (
            grant.start_minute > grant.end_minute and now.hour * 60 + now.minute < grant.end_minute
        )
        effective = today - timedelta(days=1) if overnight_tail else today
        if grant.valid_until and effective > grant.valid_until:
            continue
        if grant.valid_from and effective < grant.valid_from:
            reason = "not_started" if reason == "expired" else reason
            continue
        if grant._in_window(now):
            return "ok"
        reason = "outside_schedule"
    return reason


def grants_for(conn: sqlite3.Connection, person_id: int) -> list[Grant]:
    rows = conn.execute("SELECT * FROM grants WHERE person_id = ?", (person_id,)).fetchall()
    return [
        Grant(
            zone_id=row["zone_id"],
            weekdays=row["weekdays"],
            start_minute=row["start_minute"],
            end_minute=row["end_minute"],
            valid_from=date.fromisoformat(row["valid_from"]) if row["valid_from"] else None,
            valid_until=date.fromisoformat(row["valid_until"]) if row["valid_until"] else None,
        )
        for row in rows
    ]


def weekdays_label(mask: int) -> str:
    if mask == ALL_WEEK:
        return "Todos los días"
    if mask == 0b0011111:
        return "Lun a Vie"
    return " ".join(name for bit, name in enumerate(WEEKDAYS_ES) if mask >> bit & 1) or "Ningún día"


def minutes_label(minute: int) -> str:
    return "24:00" if minute >= 1440 else f"{minute // 60:02d}:{minute % 60:02d}"
