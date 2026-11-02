"""SQLite en modo WAL con migraciones numeradas (PRAGMA user_version)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS: list[str] = [
    """
    CREATE TABLE admins (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin', 'viewer')),
        failed_logins INTEGER NOT NULL DEFAULT 0,
        locked_until TEXT,
        created_at TEXT NOT NULL
    );
    CREATE TABLE sessions (
        token_hash TEXT PRIMARY KEY,
        admin_id INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
        csrf_token TEXT NOT NULL,
        expires_at TEXT NOT NULL
    );
    CREATE TABLE people (
        id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        document TEXT,
        group_name TEXT NOT NULL DEFAULT '',
        active INTEGER NOT NULL DEFAULT 1,
        pin_lookup TEXT UNIQUE,
        created_at TEXT NOT NULL
    );
    CREATE INDEX idx_people_name ON people(full_name);
    CREATE TABLE consents (
        id INTEGER PRIMARY KEY,
        person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
        policy_version TEXT NOT NULL,
        evidence TEXT NOT NULL,
        granted_at TEXT NOT NULL,
        recorded_by TEXT NOT NULL,
        revoked_at TEXT,
        revoked_by TEXT
    );
    CREATE INDEX idx_consents_person ON consents(person_id);
    CREATE TABLE templates (
        id INTEGER PRIMARY KEY,
        person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
        ciphertext BLOB NOT NULL,
        quality REAL NOT NULL,
        model TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE INDEX idx_templates_person ON templates(person_id);
    CREATE TABLE zones (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL DEFAULT ''
    );
    CREATE TABLE grants (
        id INTEGER PRIMARY KEY,
        person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
        zone_id INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
        weekdays INTEGER NOT NULL,
        start_minute INTEGER NOT NULL,
        end_minute INTEGER NOT NULL,
        valid_from TEXT,
        valid_until TEXT
    );
    CREATE INDEX idx_grants_person ON grants(person_id, zone_id);
    CREATE TABLE kiosks (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        zone_id INTEGER NOT NULL REFERENCES zones(id),
        token_hash TEXT NOT NULL UNIQUE,
        liveness_required INTEGER NOT NULL DEFAULT 1,
        allow_pin INTEGER NOT NULL DEFAULT 1,
        door_webhook_url TEXT,
        door_secret BLOB,
        active INTEGER NOT NULL DEFAULT 1,
        last_seen_at TEXT
    );
    -- person_id no es FK: el historial debe sobrevivir a la supresión de la persona, y el
    -- nombre vive solo en `people`, así que al suprimirla los eventos quedan seudónimos.
    CREATE TABLE events (
        id INTEGER PRIMARY KEY,
        ts TEXT NOT NULL,
        kiosk_id INTEGER,
        zone_id INTEGER,
        person_id INTEGER,
        method TEXT NOT NULL,
        outcome TEXT NOT NULL CHECK (outcome IN ('granted', 'denied')),
        reason TEXT NOT NULL,
        score REAL,
        door_status TEXT,
        photo_file TEXT,
        prev_hash TEXT NOT NULL,
        hash TEXT NOT NULL
    );
    CREATE INDEX idx_events_ts ON events(ts);
    CREATE INDEX idx_events_person ON events(person_id, ts);
    CREATE TABLE audit_log (
        id INTEGER PRIMARY KEY,
        ts TEXT NOT NULL,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        subject TEXT NOT NULL DEFAULT '',
        details TEXT NOT NULL DEFAULT '',
        prev_hash TEXT NOT NULL,
        hash TEXT NOT NULL
    );
    CREATE INDEX idx_audit_ts ON audit_log(ts);
    """,
]


def connect(path: Path | str) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    # isolation_level=None: transacciones explícitas con tx().
    conn = sqlite3.connect(path, isolation_level=None, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    # Sobrescribe con ceros lo borrado: una supresión no debe quedar en páginas libres.
    conn.execute("PRAGMA secure_delete = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    for number, script in enumerate(MIGRATIONS[version:], start=version + 1):
        conn.executescript(f"BEGIN;\n{script}\nPRAGMA user_version = {number};\nCOMMIT;")


@contextmanager
def tx(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Transacción de escritura. Reentrante: dentro de otra, se une a ella."""
    if conn.in_transaction:
        yield conn
        return
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")
