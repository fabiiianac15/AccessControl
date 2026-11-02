"""Prueba de presencia activa: la persona gira la cabeza a ambos lados en orden aleatorio.

Una foto impresa o una pantalla son planas. Al inclinarlas, cada punto se desplaza en proporción,
así que la nariz casi no se mueve respecto a los ojos. En una cabeza real sí se mueve, porque
sobresale. Inclinar mucho una foto puede confundir al detector, pero entonces los ojos se ven muy
juntos respecto a la altura del rostro: por eso cada giro también exige que esa proporción siga
cerca de la registrada. docs/evaluacion.md tiene las mediciones.

Límites conocidos (ver docs/seguridad.md): esto frena fotos y pantallas estáticas. Una secuencia
de fotos con el rostro girado, un video que responda a tiempo o una máscara 3D pueden pasarla.
Para esos casos hace falta hardware dedicado (cámara infrarroja o de profundidad).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np

LEFT = "left"
RIGHT = "right"
CENTER = "center"


def yaw_ratio(landmarks: np.ndarray) -> float:
    """Desplazamiento de la nariz respecto al punto medio de los ojos, en distancias interoculares.

    Positivo: la persona gira hacia su izquierda, que en la imagen sin espejo es hacia la derecha.
    Corrige la inclinación lateral proyectando sobre el eje que une los ojos.
    """
    right_eye, left_eye, nose = landmarks[0], landmarks[1], landmarks[2]
    axis = left_eye - right_eye
    length = float(np.hypot(*axis))
    if length < 1e-3:
        return 0.0
    return float(np.dot(nose - (right_eye + left_eye) / 2, axis / length)) / length


def face_aspect(landmarks: np.ndarray) -> float:
    """Distancia entre ojos sobre distancia de ojos a boca. Baja cuando el rostro se ve de lado."""
    right_eye, left_eye = landmarks[0], landmarks[1]
    eyes_mid = (right_eye + left_eye) / 2
    mouth_mid = (landmarks[3] + landmarks[4]) / 2
    height = float(np.hypot(*(mouth_mid - eyes_mid)))
    return float(np.hypot(*(left_eye - right_eye))) / max(height, 1e-3)


class ChallengeStatus(StrEnum):
    RUNNING = "running"
    PASSED = "passed"
    TIMED_OUT = "timed_out"


@dataclass
class Challenge:
    """Máquina de estados de una prueba: giro, centro, giro al lado contrario, centro."""

    started_at: float
    baseline_aspect: float
    timeout: float = 15.0
    turn_ratio: float = 0.28
    center_ratio: float = 0.14
    min_aspect: float = 0.65
    hold_frames: int = 2
    rng: random.Random = field(default_factory=random.SystemRandom)
    steps: list[str] = field(init=False)
    position: int = field(init=False, default=0)
    overturned: bool = field(init=False, default=False)
    _held: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        first, second = self.rng.choice([(LEFT, RIGHT), (RIGHT, LEFT)])
        self.steps = [first, CENTER, second, CENTER]

    @property
    def current(self) -> str:
        return self.steps[min(self.position, len(self.steps) - 1)]

    @property
    def at_center(self) -> bool:
        return self.current == CENTER

    def _satisfied(self, landmarks: np.ndarray) -> bool:
        step = self.current
        yaw = yaw_ratio(landmarks)
        self.overturned = False
        if step == CENTER:
            return abs(yaw) <= self.center_ratio
        # Girar hacia su izquierda desplaza la nariz a yaw positivo (ver yaw_ratio).
        turned = yaw >= self.turn_ratio if step == LEFT else yaw <= -self.turn_ratio
        if not turned:
            return False
        if face_aspect(landmarks) / self.baseline_aspect < self.min_aspect:
            self.overturned = True
            return False
        return True

    def feed(self, landmarks: np.ndarray, now: float) -> ChallengeStatus:
        if now - self.started_at > self.timeout:
            return ChallengeStatus.TIMED_OUT
        if self._satisfied(landmarks):
            self._held += 1
            if self._held >= self.hold_frames:
                self.position += 1
                self._held = 0
        else:
            self._held = 0
        return (
            ChallengeStatus.PASSED if self.position >= len(self.steps) else ChallengeStatus.RUNNING
        )
