from __future__ import annotations

import random
import re
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from portero import crypto
from portero.biometrics.engine import Face, ensure_models
from portero.config import Settings
from portero.db import connect, migrate
from portero.door import DoorClient
from portero.web.app import create_app

PASSWORD = "contrasena-de-prueba"
MODELS_DIR = Path(__file__).parents[1] / "data" / "models"
FIXTURES = Path(__file__).parent / "fixtures"


def unit(seed: int) -> np.ndarray:
    """Embedding sintético estable: cada semilla se comporta como una persona distinta."""
    vector = np.random.default_rng(seed).normal(size=128).astype(np.float32)
    return vector / np.linalg.norm(vector)


def near(vector: np.ndarray, similarity: float, seed: int = 99) -> np.ndarray:
    """Embedding con una similitud coseno exacta respecto a `vector`."""
    noise = np.random.default_rng(seed).normal(size=128).astype(np.float32)
    noise -= (noise @ vector) * vector
    noise /= np.linalg.norm(noise)
    result = similarity * vector + (1 - similarity**2) ** 0.5 * noise
    return (result / np.linalg.norm(result)).astype(np.float32)


def landmarks(yaw: float = 0.0, eye_distance: float = 80.0, height: float = 60.0) -> np.ndarray:
    """Cinco puntos con la razón nariz-ojos pedida, en un rostro centrado en (320, 240)."""
    return np.array(
        [
            [320 - eye_distance / 2, 220],
            [320 + eye_distance / 2, 220],
            [320 + yaw * eye_distance, 250],
            [295, 220 + height],
            [345, 220 + height],
        ],
        dtype=np.float32,
    )


def face(yaw: float = 0.0, box=(240.0, 150.0, 160.0, 200.0)) -> Face:
    return Face(box=box, landmarks=landmarks(yaw), score=0.95)


@dataclass
class ScriptedFrame:
    faces: list[Face]
    embedding: np.ndarray | None = None


@dataclass
class FakeEngine:
    """Reproduce un guion de cuadros. La imagen recibida se ignora, salvo para la calidad."""

    script: deque[ScriptedFrame] = field(default_factory=deque)
    current: ScriptedFrame | None = None

    def queue(self, frame_faces: list[Face], embedding: np.ndarray | None = None) -> None:
        self.script.append(ScriptedFrame(frame_faces, embedding))

    def detect(self, image):
        self.current = self.script.popleft() if self.script else ScriptedFrame([])
        return self.current.faces

    def embed(self, image, _face):
        assert self.current is not None and self.current.embedding is not None
        return self.current.embedding


class RecordingDoor(DoorClient):
    def __init__(self, result: str = "opened") -> None:
        super().__init__()
        self.calls: list[dict] = []
        self.result = result

    def open(self, url, secret, payload):
        self.calls.append({"url": url, "secret": secret, "payload": payload})
        return self.result


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(_env_file=None, data_dir=tmp_path, org_name="UFPSO Pruebas")


@pytest.fixture
def conn(settings):
    connection = connect(settings.db_path)
    migrate(connection)
    yield connection
    connection.close()


@pytest.fixture
def engine() -> FakeEngine:
    return FakeEngine()


@pytest.fixture
def door() -> RecordingDoor:
    return RecordingDoor()


@pytest.fixture
def app(settings, engine, door):
    return create_app(settings, engine=engine, door=door)


@pytest.fixture
def state(app):
    return app.state.portero


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def frame_bytes() -> bytes:
    """JPEG con textura y brillo medios: pasa el filtro de calidad sobre la caja de `face()`."""
    rng = np.random.default_rng(7)
    image = rng.integers(60, 200, size=(480, 640, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    assert ok
    return encoded.tobytes()


def create_admin(conn, username="coordinador", role="admin") -> None:
    conn.execute(
        "INSERT INTO admins (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (username, crypto.hash_password(PASSWORD), role, "2026-01-01T00:00:00+00:00"),
    )


def login(client: TestClient, username="coordinador") -> str:
    """Inicia sesión y devuelve el token CSRF que trae el panel."""
    response = client.post("/login", data={"username": username, "password": PASSWORD})
    assert response.status_code == 303, response.text
    page = client.get("/cuenta")
    return re.search(r'name="csrf" value="([^"]+)"', page.text).group(1)


@pytest.fixture
def admin_client(client, state) -> tuple[TestClient, str]:
    with state.db() as connection:
        create_admin(connection)
    return client, login(client)


def seed_person(connection, name="Camilo Quintero", consent=True) -> int:
    person_id = connection.execute(
        "INSERT INTO people (full_name, created_at) VALUES (?, ?)",
        (name, "2026-01-01T00:00:00+00:00"),
    ).lastrowid
    if consent:
        connection.execute(
            """INSERT INTO consents (person_id, policy_version, evidence, granted_at, recorded_by)
               VALUES (?, '2026-11', 'folio 1', '2026-01-01T00:00:00+00:00', 'prueba')""",
            (person_id,),
        )
    return person_id


def seed_zone_and_kiosk(state, connection, liveness=True, webhook=None) -> tuple[int, str]:
    zone = connection.execute("INSERT INTO zones (name) VALUES ('Laboratorio')").lastrowid
    token = crypto.new_token()
    kiosk = connection.execute(
        """INSERT INTO kiosks (name, zone_id, token_hash, liveness_required, door_webhook_url)
           VALUES ('Entrada', ?, ?, ?, ?)""",
        (zone, crypto.token_hash(token), 1 if liveness else 0, webhook),
    ).lastrowid
    if webhook:
        from portero.access import door_context

        connection.execute(
            "UPDATE kiosks SET door_secret = ? WHERE id = ?",
            (state.keys.encrypt(b"secreto-puerta", door_context(kiosk)), kiosk),
        )
    return zone, token


def grant_all(connection, person_id: int, zone_id: int) -> None:
    connection.execute(
        """INSERT INTO grants (person_id, zone_id, weekdays, start_minute, end_minute)
           VALUES (?, ?, 127, 0, 1440)""",
        (person_id, zone_id),
    )


def enroll(state, connection, person_id: int, embedding: np.ndarray) -> None:
    from portero.biometrics.gallery import pack_template, template_context
    from portero.biometrics.liveness import face_aspect

    connection.execute(
        """INSERT INTO templates (person_id, ciphertext, quality, model, created_at)
           VALUES (?, ?, 1.0, 'prueba', '2026-01-01T00:00:00+00:00')""",
        (
            person_id,
            state.keys.encrypt(
                pack_template(embedding, face_aspect(landmarks())), template_context(person_id)
            ),
        ),
    )
    state.gallery.reload(connection, state.keys)


@pytest.fixture
def fixed_rng() -> random.Random:
    return random.Random(3)


@pytest.fixture(scope="session")
def real_models() -> Path:
    try:
        ensure_models(MODELS_DIR)
    except OSError as error:
        pytest.skip(f"No se pudieron obtener los modelos: {error}")
    return MODELS_DIR


FIXED_NOW = datetime(2026, 3, 4, 15, 0, tzinfo=UTC)  # miércoles 10:00 en Bogotá
