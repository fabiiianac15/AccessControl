"""Galería en memoria de plantillas descifradas y su comparación 1:N."""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass

import numpy as np

from ..crypto import Keyring

EMBEDDING_SIZE = 128


@dataclass(frozen=True)
class Match:
    person_id: int | None
    score: float
    runner_up: float


def template_context(person_id: int) -> str:
    return f"template:{person_id}"


def pack_template(embedding: np.ndarray, aspect: float) -> bytes:
    """Lo que se cifra: la plantilla y la proporción del rostro de esa muestra."""
    return np.append(embedding.astype(np.float32), np.float32(aspect)).tobytes()


class Gallery:
    """Solo carga plantillas de personas activas con autorización vigente."""

    def __init__(self, threshold: float, margin: float) -> None:
        self.threshold = threshold
        self.margin = margin
        self._lock = threading.Lock()
        self._matrix = np.empty((0, EMBEDDING_SIZE), dtype=np.float32)
        self._owners = np.empty(0, dtype=np.int64)
        self._aspects: dict[int, float] = {}

    def reload(self, conn: sqlite3.Connection, keys: Keyring) -> None:
        rows = conn.execute(
            """SELECT t.person_id, t.ciphertext FROM templates t
               JOIN people p ON p.id = t.person_id
               WHERE p.active = 1 AND EXISTS (
                   SELECT 1 FROM consents c WHERE c.person_id = p.id AND c.revoked_at IS NULL)"""
        ).fetchall()
        records = [
            np.frombuffer(
                keys.decrypt(row["ciphertext"], template_context(row["person_id"])),
                dtype=np.float32,
            )
            for row in rows
        ]
        matrix = (
            np.vstack([record[:EMBEDDING_SIZE] for record in records])
            if records
            else np.empty((0, EMBEDDING_SIZE), dtype=np.float32)
        )
        owners = np.array([row["person_id"] for row in rows], dtype=np.int64)
        by_person: dict[int, list[float]] = {}
        for owner, record in zip(owners.tolist(), records, strict=True):
            by_person.setdefault(owner, []).append(float(record[EMBEDDING_SIZE]))
        aspects = {owner: float(np.median(values)) for owner, values in by_person.items()}
        with self._lock:
            self._matrix, self._owners, self._aspects = matrix, owners, aspects

    def enrolled_aspect(self, person_id: int) -> float | None:
        """Proporción del rostro al registrarse: una base que el atacante no puede falsear."""
        return self._aspects.get(person_id)

    def size(self) -> int:
        return len(set(self._owners.tolist()))

    def best(self, embedding: np.ndarray, exclude: int | None = None) -> tuple[int | None, float]:
        """Mejor persona por similitud, sin aplicar umbrales."""
        with self._lock:
            matrix, owners = self._matrix, self._owners
        if exclude is not None:
            keep = owners != exclude
            matrix, owners = matrix[keep], owners[keep]
        if len(owners) == 0:
            return None, -1.0
        scores = matrix @ embedding
        index = int(np.argmax(scores))
        return int(owners[index]), float(scores[index])

    def score_for(self, embedding: np.ndarray, person_id: int) -> float:
        with self._lock:
            matrix, owners = self._matrix, self._owners
        selected = matrix[owners == person_id]
        return float((selected @ embedding).max()) if len(selected) else -1.0

    def match(self, embedding: np.ndarray) -> Match:
        """Acepta solo si supera el umbral y la segunda persona queda a distancia suficiente."""
        person, score = self.best(embedding)
        if person is None:
            return Match(None, score, -1.0)
        _, runner_up = self.best(embedding, exclude=person)
        accepted = score >= self.threshold and score - runner_up >= self.margin
        return Match(person if accepted else None, score, runner_up)
