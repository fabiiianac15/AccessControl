"""Consultas de lectura: tablero, eventos, asistencia y CSV."""

from __future__ import annotations

import csv
import io
import sqlite3
from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from . import ledger


def day_bounds(day: date, tz: ZoneInfo) -> tuple[str, str]:
    start = datetime.combine(day, time.min, tz)
    return ledger.iso(start), ledger.iso(start + timedelta(days=1))


def to_local(ts: str, tz: ZoneInfo) -> datetime:
    return datetime.fromisoformat(ts).astimezone(tz)


_EVENT_SELECT = """
    SELECT e.*, p.full_name, p.group_name, z.name AS zone_name, k.name AS kiosk_name
    FROM events e
    LEFT JOIN people p ON p.id = e.person_id
    LEFT JOIN zones z ON z.id = e.zone_id
    LEFT JOIN kiosks k ON k.id = e.kiosk_id
"""


def list_events(
    conn: sqlite3.Connection,
    *,
    start: str | None = None,
    end: str | None = None,
    outcome: str | None = None,
    zone_id: int | None = None,
    person_id: int | None = None,
    search: str | None = None,
    limit: int = 200,
) -> list[sqlite3.Row]:
    where, params = [], []
    for clause, value in (
        ("e.ts >= ?", start),
        ("e.ts < ?", end),
        ("e.outcome = ?", outcome),
        ("e.zone_id = ?", zone_id),
        ("e.person_id = ?", person_id),
    ):
        if value is not None and value != "":
            where.append(clause)
            params.append(value)
    if search:
        where.append("p.full_name LIKE ? ESCAPE '\\'")
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        params.append(f"%{escaped}%")
    condition = f"WHERE {' AND '.join(where)}" if where else ""
    return conn.execute(
        f"{_EVENT_SELECT} {condition} ORDER BY e.id DESC LIMIT ?", (*params, limit)
    ).fetchall()


def dashboard(conn: sqlite3.Connection, tz: ZoneInfo, now: datetime) -> dict:
    local = now.astimezone(tz)
    start, end = day_bounds(local.date(), tz)
    rows = conn.execute(
        "SELECT ts, outcome, reason, person_id FROM events WHERE ts >= ? AND ts < ?", (start, end)
    ).fetchall()

    hours = [{"hour": hour, "granted": 0, "denied": 0} for hour in range(24)]
    present: set[int] = set()
    for row in rows:
        hours[to_local(row["ts"], tz).hour][row["outcome"]] += 1
        if row["outcome"] == "granted" and row["person_id"] is not None:
            present.add(row["person_id"])

    granted = sum(hour["granted"] for hour in hours)
    denied = sum(hour["denied"] for hour in hours)

    pending = conn.execute(
        """SELECT COUNT(*) FROM people p WHERE p.active = 1
           AND p.pin_lookup IS NULL
           AND NOT EXISTS (SELECT 1 FROM templates t WHERE t.person_id = p.id)"""
    ).fetchone()[0]
    stale_after = ledger.iso(now - timedelta(minutes=5))
    kiosks = conn.execute("SELECT * FROM kiosks WHERE active = 1 ORDER BY name").fetchall()
    offline = [
        k["name"] for k in kiosks if not k["last_seen_at"] or k["last_seen_at"] < stale_after
    ]

    # Patrón de ataque: muchos rechazos del mismo tipo en la última hora.
    hour_ago = ledger.iso(now - timedelta(hours=1))
    suspicious = conn.execute(
        """SELECT reason, COUNT(*) AS total FROM events
           WHERE outcome = 'denied' AND ts >= ? AND reason IN
             ('liveness_failed', 'identity_changed', 'pin_invalid', 'pin_locked', 'unknown_face')
           GROUP BY reason HAVING total >= 5 ORDER BY total DESC""",
        (hour_ago,),
    ).fetchall()

    return {
        "granted": granted,
        "denied": denied,
        "present": len(present),
        "hours": hours,
        "pending_people": pending,
        "kiosks_total": len(kiosks),
        "kiosks_offline": offline,
        "suspicious": suspicious,
        "people_total": conn.execute("SELECT COUNT(*) FROM people").fetchone()[0],
    }


def attendance(
    conn: sqlite3.Connection,
    tz: ZoneInfo,
    start_day: date,
    end_day: date,
    group: str | None = None,
) -> list[dict]:
    """Primera y última marcación autorizada por persona y día, en hora local."""
    start, _ = day_bounds(start_day, tz)
    _, end = day_bounds(end_day, tz)
    query = """SELECT e.ts, e.person_id, p.full_name, p.group_name
               FROM events e JOIN people p ON p.id = e.person_id
               WHERE e.outcome = 'granted' AND e.ts >= ? AND e.ts < ?"""
    params: list[str] = [start, end]
    if group:
        query += " AND p.group_name = ?"
        params.append(group)

    days: dict[tuple[date, int], dict] = {}
    for row in conn.execute(query + " ORDER BY e.ts", params):
        moment = to_local(row["ts"], tz)
        entry = days.setdefault(
            (moment.date(), row["person_id"]),
            {
                "day": moment.date(),
                "person_id": row["person_id"],
                "name": row["full_name"],
                "group": row["group_name"],
                "first": moment,
                "last": moment,
                "marks": 0,
            },
        )
        entry["last"] = moment
        entry["marks"] += 1
    for entry in days.values():
        entry["hours"] = round((entry["last"] - entry["first"]).total_seconds() / 3600, 2)
    return sorted(days.values(), key=lambda e: (e["day"], e["name"]), reverse=True)


def csv_safe(value: object) -> str:
    """Neutraliza fórmulas: Excel ejecutaría una celda que empiece por =, +, - o @."""
    text = "" if value is None else str(value)
    return f"'{text}" if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def to_csv(header: Iterable[str], rows: Iterable[Iterable[object]]) -> str:
    """CSV con BOM y punto y coma: así lo abre bien Excel con configuración regional de Colombia."""
    buffer = io.StringIO()
    buffer.write("﻿")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(header)
    for row in rows:
        writer.writerow([csv_safe(cell) for cell in row])
    return buffer.getvalue()
