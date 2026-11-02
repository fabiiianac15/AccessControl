"""Dependencias compartidas de la aplicación en ejecución."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

from .biometrics.engine import FaceEngine
from .biometrics.gallery import Gallery
from .config import Settings
from .crypto import Keyring
from .db import connect
from .door import DoorClient
from .ledger import utcnow


@dataclass
class AppState:
    settings: Settings
    keys: Keyring
    engine: FaceEngine
    gallery: Gallery
    door: DoorClient
    clock: Callable[[], datetime] = utcnow

    @contextmanager
    def db(self) -> Iterator[sqlite3.Connection]:
        conn = connect(self.settings.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def local_now(self) -> datetime:
        return self.clock().astimezone(self.settings.tz)

    def reload_gallery(self) -> None:
        with self.db() as conn:
            self.gallery.reload(conn, self.keys)
