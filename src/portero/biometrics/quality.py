"""Filtro de calidad: rechaza a tiempo los cuadros que producirían plantillas malas."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .engine import Face
from .liveness import yaw_ratio

HINTS = {
    "too_small": "Acércate un poco",
    "off_frame": "Ubica tu rostro en el centro",
    "too_dark": "Falta luz sobre tu rostro",
    "too_bright": "Hay demasiada luz directa",
    "blurry": "Quédate quieto un momento",
    "not_frontal": "Mira de frente a la cámara",
}


@dataclass(frozen=True)
class Quality:
    ok: bool
    issue: str | None
    score: float


def assess(
    image: np.ndarray,
    face: Face,
    *,
    min_eye_distance: float = 32.0,
    max_yaw: float = 0.2,
) -> Quality:
    height, width = image.shape[:2]
    x, y, w, h = face.box
    # El alineado necesita el rostro entero: un recorte contra el borde degrada la plantilla.
    if x < 0 or y < 0 or x + w > width or y + h > height:
        return Quality(False, "off_frame", 0.0)

    eyes = face.landmarks[1] - face.landmarks[0]
    eye_distance = float(np.hypot(*eyes))
    if eye_distance < min_eye_distance:
        return Quality(False, "too_small", 0.0)

    crop = image[int(y) : int(y + h), int(x) : int(x + w)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    if brightness < 50:
        return Quality(False, "too_dark", 0.0)
    if brightness > 215:
        return Quality(False, "too_bright", 0.0)

    # Varianza del Laplaciano normalizada a un tamaño fijo para no premiar rostros grandes.
    sharpness = float(cv2.Laplacian(cv2.resize(gray, (112, 112)), cv2.CV_64F).var())
    if sharpness < 25:
        return Quality(False, "blurry", 0.0)

    yaw = yaw_ratio(face.landmarks)
    if abs(yaw) > max_yaw:
        return Quality(False, "not_frontal", 0.0)

    size_part = min(eye_distance / 80.0, 1.0)
    sharp_part = min(sharpness / 200.0, 1.0)
    pose_part = 1.0 - abs(yaw) / max_yaw
    return Quality(True, None, round(0.4 * size_part + 0.4 * sharp_part + 0.2 * pose_part, 3))
