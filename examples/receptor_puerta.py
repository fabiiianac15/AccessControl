"""Receptor de puerta: verifica el aviso firmado de Portero y activa el relé.

Pensado para una Raspberry Pi junto a la puerta. Solo usa la biblioteca estándar.

    PUERTA_SECRETO=... python receptor_puerta.py

En el panel, la URL de la puerta sería http://<ip-de-la-pi>:9000/abrir. Para mover un relé real,
reemplaza `abrir_cerradura` (por ejemplo con gpiozero: OutputDevice(17).blink(on_time=3, n=1)).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_CLOCK_SKEW_SECONDS = 30
MAX_BODY = 4096


def abrir_cerradura() -> None:
    print("Cerradura abierta")


def firma_valida(secreto: str, marca: str, cuerpo: bytes, firma: str, ahora: float) -> bool:
    try:
        if abs(ahora - int(marca)) > MAX_CLOCK_SKEW_SECONDS:
            return False
    except ValueError:
        return False
    esperada = hmac.new(secreto.encode(), marca.encode() + b"." + cuerpo, hashlib.sha256)
    return hmac.compare_digest(esperada.hexdigest(), firma)


class Receptor(BaseHTTPRequestHandler):
    secreto = ""
    # Dentro de la ventana de tiempo, un aviso capturado en la red no debe abrir dos veces.
    ya_vistos: dict[int, float] = {}

    def _responder(self, codigo: int) -> None:
        self.send_response(codigo)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 - nombre exigido por http.server
        longitud = int(self.headers.get("Content-Length", "0"))
        if self.path != "/abrir" or not 0 < longitud <= MAX_BODY:
            self._responder(400)
            return
        cuerpo = self.rfile.read(longitud)
        ahora = time.time()
        marca = self.headers.get("X-Portero-Timestamp", "")
        firma = self.headers.get("X-Portero-Signature", "")
        if not firma_valida(self.secreto, marca, cuerpo, firma, ahora):
            self._responder(401)
            return

        evento = int(json.loads(cuerpo)["event"])
        vencidos = [e for e, t in self.ya_vistos.items() if ahora - t > 2 * MAX_CLOCK_SKEW_SECONDS]
        for viejo in vencidos:
            del self.ya_vistos[viejo]
        if evento in self.ya_vistos:
            self._responder(409)
            return
        self.ya_vistos[evento] = ahora

        abrir_cerradura()
        self._responder(200)


def main() -> None:
    Receptor.secreto = os.environ["PUERTA_SECRETO"]
    ThreadingHTTPServer(("0.0.0.0", 9000), Receptor).serve_forever()  # noqa: S104


if __name__ == "__main__":
    main()
