"""Motor facial sobre YuNet (detección) y SFace (plantillas), ambos ejecutados por OpenCV.

No requiere compilar dlib ni GPU. Los modelos se descargan una vez y se verifican con SHA-256.
"""

from __future__ import annotations

import hashlib
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

_ZOO = "https://github.com/opencv/opencv_zoo/raw/main/models"
DETECTOR_FILE = "face_detection_yunet_2023mar.onnx"
RECOGNIZER_FILE = "face_recognition_sface_2021dec.onnx"
MODEL_NAME = "sface_2021dec"
MODELS = {
    DETECTOR_FILE: (
        f"{_ZOO}/face_detection_yunet/{DETECTOR_FILE}",
        "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
    ),
    RECOGNIZER_FILE: (
        f"{_ZOO}/face_recognition_sface/{RECOGNIZER_FILE}",
        "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
    ),
}


@dataclass(frozen=True)
class Face:
    box: tuple[float, float, float, float]  # x, y, ancho, alto
    landmarks: np.ndarray  # 5x2: ojo derecho, ojo izquierdo, nariz, boca der., boca izq.
    score: float
    raw: np.ndarray | None = None  # fila original de YuNet, la pide alignCrop

    @property
    def area(self) -> float:
        return self.box[2] * self.box[3]


class FaceEngine(Protocol):
    def detect(self, image: np.ndarray) -> list[Face]: ...

    def embed(self, image: np.ndarray, face: Face) -> np.ndarray: ...


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_models(models_dir: Path) -> None:
    models_dir.mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in MODELS.items():
        path = models_dir / name
        if path.exists() and _sha256(path) == expected:
            continue
        partial = path.with_suffix(".part")
        print(f"Descargando {name}...")
        urllib.request.urlretrieve(url, partial)  # noqa: S310  (URL fija https)
        actual = _sha256(partial)
        if actual != expected:
            partial.unlink()
            raise RuntimeError(f"{name}: SHA-256 inesperado ({actual}). No se instaló.")
        partial.replace(path)


class OpenCVFaceEngine:
    """Las redes de OpenCV no son seguras entre hilos: un candado serializa la inferencia."""

    def __init__(self, models_dir: Path, min_detection_score: float = 0.8) -> None:
        self._lock = threading.Lock()
        self._detector = cv2.FaceDetectorYN.create(
            str(models_dir / DETECTOR_FILE), "", (320, 320), min_detection_score, 0.3, 50
        )
        self._recognizer = cv2.FaceRecognizerSF.create(str(models_dir / RECOGNIZER_FILE), "")

    def detect(self, image: np.ndarray) -> list[Face]:
        height, width = image.shape[:2]
        with self._lock:
            self._detector.setInputSize((width, height))
            _, rows = self._detector.detect(image)
        if rows is None:
            return []
        faces = [
            Face(
                box=(float(r[0]), float(r[1]), float(r[2]), float(r[3])),
                landmarks=np.asarray(r[4:14], dtype=np.float32).reshape(5, 2),
                score=float(r[14]),
                raw=np.asarray(r, dtype=np.float32).copy(),
            )
            for r in rows
        ]
        return sorted(faces, key=lambda face: face.area, reverse=True)

    def embed(self, image: np.ndarray, face: Face) -> np.ndarray:
        if face.raw is None:
            raise ValueError("El rostro no viene de este detector")
        with self._lock:
            aligned = self._recognizer.alignCrop(image, face.raw)
            feature = self._recognizer.feature(aligned)
        vector = np.asarray(feature, dtype=np.float32).ravel().copy()
        return vector / np.linalg.norm(vector)


def decode_image(data: bytes, max_side: int = 1280) -> np.ndarray | None:
    """Decodifica JPEG/PNG sin confiar en el cliente. Devuelve None si no es una imagen válida."""
    if not data:
        return None
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return None
    longest = max(image.shape[:2])
    if longest > max_side:
        scale = max_side / longest
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return image
