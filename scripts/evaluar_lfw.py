"""Mide el motor facial con pares etiquetados de LFW y escribe la tabla de umbrales.

Uso:
    curl -LO https://huggingface.co/datasets/logasja/lfw/resolve/main/pairs/test-00000-of-00001.parquet
    curl -LO https://huggingface.co/datasets/logasja/lfw/resolve/main/pairs/train-00000-of-00001.parquet
    uv run --with pyarrow python scripts/evaluar_lfw.py data/models *.parquet
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from portero.biometrics.engine import OpenCVFaceEngine, decode_image


def central_face(engine, image):
    faces = engine.detect(image)
    if not faces:
        return None
    # LFW centra al sujeto: en fotos con varias personas, el rostro más cercano al centro.
    height, width = image.shape[:2]
    return min(
        faces,
        key=lambda f: (
            (f.box[0] + f.box[2] / 2 - width / 2) ** 2 + (f.box[1] + f.box[3] / 2 - height / 2) ** 2
        ),
    )


def main() -> None:
    engine = OpenCVFaceEngine(Path(sys.argv[1]), min_detection_score=0.6)
    scores: list[float] = []
    labels: list[int] = []
    undetected = 0
    for name in sys.argv[2:]:
        table = pq.read_table(name)
        for row in table.to_pylist():
            embeddings = []
            for column in ("img_0", "img_1"):
                image = decode_image(row[column]["bytes"])
                face = central_face(engine, image)
                if face is None:
                    break
                embeddings.append(engine.embed(image, face))
            if len(embeddings) < 2:
                undetected += 1
                continue
            scores.append(float(embeddings[0] @ embeddings[1]))
            labels.append(int(row["pair"]))

    score_array, label_array = np.array(scores), np.array(labels)
    genuine, impostor = score_array[label_array == 1], score_array[label_array == 0]
    print(
        f"Pares: {len(scores)} (mismos {len(genuine)}, distintos {len(impostor)}); "
        f"sin rostro detectado: {undetected}"
    )
    print(f"Media mismos {genuine.mean():.3f} | Media distintos {impostor.mean():.3f}\n")
    print("| Umbral | Falsa aceptación | Falso rechazo |")
    print("|---|---|---|")
    for threshold in (0.30, 0.363, 0.40, 0.45, 0.50, 0.55, 0.60):
        far = (impostor >= threshold).mean() * 100
        frr = (genuine < threshold).mean() * 100
        print(f"| {threshold:.3f} | {far:.2f} % | {frr:.2f} % |")


if __name__ == "__main__":
    main()
