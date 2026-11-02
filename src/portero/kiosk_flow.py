"""Flujo del kiosco: de cuadros de cámara a una decisión. Todo se decide en el servidor."""

from __future__ import annotations

import random
import sqlite3
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from . import access, policy
from .biometrics import quality
from .biometrics.engine import Face
from .biometrics.liveness import CENTER, Challenge, ChallengeStatus
from .crypto import Keyring
from .state import AppState

RESULT_SECONDS = 4.0
CONFIRM_FRAMES = 2  # cuadros seguidos con la misma identidad antes de iniciar la prueba
UNKNOWN_FRAMES = 4  # cuadros buenos sin coincidencia antes de denegar
FACE_LOST_SECONDS = 3.0
# Dos rostros cuentan como "más de una persona" si el segundo supera esta fracción del primero.
SECOND_FACE_RATIO = 0.35
# Un perfil se parece menos a la plantilla frontal: durante los giros basta con no ser otra persona.
TURN_CONTINUITY_MIN = 0.2
CONTINUITY_MAX_MISSES = 3
PIN_FORGET_SECONDS = 6 * 3600


@dataclass
class KioskSession:
    candidate: int | None = None
    candidate_frames: int = 0
    unknown_frames: int = 0
    low_similarity_frames: int = 0
    best_score: float | None = None
    challenge: Challenge | None = None
    anchor: np.ndarray | None = None
    last_face_at: float = 0.0
    result: dict | None = None
    result_until: float = 0.0
    pin_failures: int = 0
    pin_lockouts: int = 0
    pin_last_failure: float = 0.0
    pin_locked_until: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def reset(self) -> None:
        self.candidate = None
        self.candidate_frames = 0
        self.unknown_frames = 0
        self.low_similarity_frames = 0
        self.best_score = None
        self.challenge = None
        self.anchor = None


def _guide(hint: str, box: list[float] | None = None) -> dict:
    return {"phase": "guide", "hint": hint, "message": _MESSAGES[hint], "box": box}


_MESSAGES = {
    "no_face": "Mira a la cámara",
    "one_person": "Una persona a la vez",
    "checking": "Un momento",
    "no_people": "Aún no hay personas registradas",
    **quality.HINTS,
}


def _normalized_box(face: Face, image: np.ndarray) -> list[float]:
    height, width = image.shape[:2]
    x, y, w, h = face.box
    return [round(x / width, 4), round(y / height, 4), round(w / width, 4), round(h / height, 4)]


class KioskFlow:
    def __init__(
        self,
        state: AppState,
        monotonic: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
    ) -> None:
        self.state = state
        self._now = monotonic
        self._rng = rng
        self._sessions: dict[int, KioskSession] = {}
        self._registry_lock = threading.Lock()

    @property
    def keys(self) -> Keyring:
        return self.state.keys

    def session(self, kiosk_id: int) -> KioskSession:
        with self._registry_lock:
            return self._sessions.setdefault(kiosk_id, KioskSession())

    def process_frame(
        self, conn: sqlite3.Connection, kiosk: sqlite3.Row, image: np.ndarray
    ) -> dict:
        session = self.session(kiosk["id"])
        with session.lock:
            try:
                return self._process(conn, kiosk, session, image)
            except Exception:
                # Falla cerrada: se descarta la prueba en curso y la puerta no se abre.
                session.reset()
                raise

    def _process(
        self, conn: sqlite3.Connection, kiosk: sqlite3.Row, session: KioskSession, image: np.ndarray
    ) -> dict:
        now = self._now()
        if session.result is not None:
            if now < session.result_until:
                return session.result
            session.result = None
            session.reset()

        faces = self.state.engine.detect(image)
        if not faces:
            if session.challenge is None or now - session.last_face_at > FACE_LOST_SECONDS:
                session.reset()
            return _guide("no_face")

        session.last_face_at = now
        face = faces[0]
        box = _normalized_box(face, image)
        if len(faces) > 1 and faces[1].area > face.area * SECOND_FACE_RATIO:
            session.reset()
            return _guide("one_person", box)

        if session.challenge is not None:
            return self._advance_challenge(conn, kiosk, session, image, face, box, now)
        return self._identify(conn, kiosk, session, image, face, box, now)

    def _identify(
        self,
        conn: sqlite3.Connection,
        kiosk: sqlite3.Row,
        session: KioskSession,
        image: np.ndarray,
        face: Face,
        box: list[float],
        now: float,
    ) -> dict:
        check = quality.assess(image, face)
        if not check.ok:
            session.candidate_frames = 0
            return _guide(check.issue or "checking", box)

        embedding = self.state.engine.embed(image, face)
        match = self.state.gallery.match(embedding)

        if match.person_id is None:
            session.candidate = None
            session.candidate_frames = 0
            session.unknown_frames += 1
            if session.unknown_frames >= UNKNOWN_FRAMES:
                return self._finish(
                    conn,
                    kiosk,
                    session,
                    now,
                    person_id=None,
                    denial="unknown_face",
                    score=match.score,
                    frame=image,
                )
            return _guide("checking", box)

        session.unknown_frames = 0
        if match.person_id == session.candidate:
            session.candidate_frames += 1
        else:
            session.candidate = match.person_id
            session.candidate_frames = 1
        session.best_score = match.score

        if session.candidate_frames < CONFIRM_FRAMES:
            return _guide("checking", box)

        if kiosk["liveness_required"]:
            baseline = self.state.gallery.enrolled_aspect(match.person_id)
            if baseline is None:  # la galería cambió justo ahora: se reintenta con otro cuadro
                return _guide("checking", box)
            settings = self.state.settings
            session.challenge = Challenge(
                started_at=now,
                baseline_aspect=baseline,
                timeout=settings.liveness_timeout_seconds,
                turn_ratio=settings.liveness_turn_ratio,
                center_ratio=settings.liveness_center_ratio,
                min_aspect=settings.liveness_min_aspect,
                rng=self._rng or random.SystemRandom(),
            )
            session.anchor = embedding
            return self._challenge_view(session, box)

        return self._finish(
            conn,
            kiosk,
            session,
            now,
            person_id=match.person_id,
            score=match.score,
            frame=image,
        )

    def _advance_challenge(
        self,
        conn: sqlite3.Connection,
        kiosk: sqlite3.Row,
        session: KioskSession,
        image: np.ndarray,
        face: Face,
        box: list[float],
        now: float,
    ) -> dict:
        challenge = session.challenge
        assert challenge is not None and session.anchor is not None
        person_id = session.candidate
        score = session.best_score
        assert person_id is not None

        # Continuidad durante los giros: un cuadro borroso se tolera, varios seguidos no.
        embedding = self.state.engine.embed(image, face)
        if float(session.anchor @ embedding) < TURN_CONTINUITY_MIN:
            session.low_similarity_frames += 1
            if session.low_similarity_frames >= CONTINUITY_MAX_MISSES:
                return self._finish(
                    conn,
                    kiosk,
                    session,
                    now,
                    person_id=person_id,
                    denial="identity_changed",
                    score=score,
                    frame=image,
                )
        else:
            session.low_similarity_frames = 0

        status = challenge.feed(face.landmarks, now)
        if status is ChallengeStatus.TIMED_OUT:
            return self._finish(
                conn,
                kiosk,
                session,
                now,
                person_id=person_id,
                denial="liveness_failed",
                score=score,
                frame=image,
            )
        if status is ChallengeStatus.PASSED:
            # Última barrera: de frente, quien termina debe superar el umbral completo. Si este
            # cuadro no alcanza se pide otro, y un impostor agotará el tiempo sin pasar.
            final_score = self.state.gallery.score_for(embedding, person_id)
            if final_score >= self.state.gallery.threshold:
                return self._finish(
                    conn,
                    kiosk,
                    session,
                    now,
                    person_id=person_id,
                    score=final_score,
                    frame=image,
                )
            challenge.position = len(challenge.steps) - 1
        return self._challenge_view(session, box)

    def _challenge_view(self, session: KioskSession, box: list[float]) -> dict:
        challenge = session.challenge
        assert challenge is not None
        direction = challenge.current
        message = {
            "left": "Gira la cabeza a tu izquierda",
            "right": "Gira la cabeza a tu derecha",
            CENTER: "Vuelve a mirar al frente",
        }[direction]
        if challenge.overturned:
            message = "Gira un poco menos"
        return {
            "phase": "challenge",
            "direction": direction,
            "step": challenge.position + 1,
            "total": len(challenge.steps),
            "message": message,
            "box": box,
        }

    def _finish(
        self,
        conn: sqlite3.Connection,
        kiosk: sqlite3.Row,
        session: KioskSession,
        now: float,
        *,
        person_id: int | None,
        denial: str | None = None,
        score: float | None = None,
        frame: np.ndarray | None = None,
    ) -> dict:
        outcome = access.conclude(
            self.state,
            conn,
            kiosk,
            person_id=person_id,
            method="face",
            denial=denial,
            score=score,
            frame=frame,
        )
        return self._show_result(session, outcome, now)

    def _show_result(self, session: KioskSession, outcome: access.Outcome, now: float) -> dict:
        session.reset()
        # Sin confirmar la identidad no se revela un nombre: alguien con una foto no debe
        # enterarse de a quién pertenece ni de qué horario tiene.
        reveals_name = outcome.granted or outcome.reason in {
            "no_grant",
            "outside_schedule",
            "not_started",
            "expired",
            "inactive",
        }
        session.result = {
            "phase": "result",
            "granted": outcome.granted,
            "reason": outcome.reason,
            "message": policy.REASONS[outcome.reason],
            "name": outcome.first_name if reveals_name else None,
            "door": outcome.door_status,
        }
        session.result_until = now + RESULT_SECONDS
        return session.result

    def submit_pin(self, conn: sqlite3.Connection, kiosk: sqlite3.Row, pin: str) -> dict:
        session = self.session(kiosk["id"])
        settings = self.state.settings
        with session.lock:
            now = self._now()
            if now < session.pin_locked_until:
                return {
                    "phase": "pin_locked",
                    "message": policy.REASONS["pin_locked"],
                    "retry_in": round(session.pin_locked_until - now),
                }
            row = conn.execute(
                "SELECT id FROM people WHERE pin_lookup = ?", (self.keys.pin_lookup(pin),)
            ).fetchone()
            if row is None:
                # El contador solo olvida con el tiempo. Si un PIN correcto lo reiniciara, alguien
                # con PIN propio podría intercalarlo para probar los de otros sin límite.
                if now - session.pin_last_failure > PIN_FORGET_SECONDS:
                    session.pin_failures = 0
                    session.pin_lockouts = 0
                session.pin_last_failure = now
                session.pin_failures += 1
                locked = session.pin_failures >= settings.pin_max_failures
                if locked:
                    # Cada bloqueo dura el doble: limita los intentos por día, no solo por minuto.
                    wait = settings.pin_lockout_seconds * 2**session.pin_lockouts
                    session.pin_failures = 0
                    session.pin_lockouts += 1
                    session.pin_locked_until = now + min(wait, settings.pin_lockout_max_seconds)
                outcome = access.conclude(
                    self.state,
                    conn,
                    kiosk,
                    person_id=None,
                    method="pin",
                    denial="pin_locked" if locked else "pin_invalid",
                )
                return self._show_result(session, outcome, now)
            outcome = access.conclude(self.state, conn, kiosk, person_id=row["id"], method="pin")
            return self._show_result(session, outcome, now)
