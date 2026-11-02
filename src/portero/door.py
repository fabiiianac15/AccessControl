"""Aviso firmado a la puerta (relé, ESP32, Raspberry Pi o lo que reciba un webhook)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import httpx

MAX_CLOCK_SKEW_SECONDS = 30


def sign(secret: str, timestamp: str, body: bytes) -> str:
    return hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()


def verify_signature(
    secret: str,
    timestamp: str,
    body: bytes,
    signature: str,
    now: float | None = None,
) -> bool:
    """Verificación para el receptor. La ventana de tiempo limita la repetición de un aviso."""
    try:
        age = abs((time.time() if now is None else now) - int(timestamp))
    except ValueError:
        return False
    return age <= MAX_CLOCK_SKEW_SECONDS and hmac.compare_digest(
        sign(secret, timestamp, body), signature
    )


class DoorClient:
    def __init__(self, timeout: float = 2.0) -> None:
        self._timeout = timeout

    def open(self, url: str, secret: str, payload: dict) -> str:
        """Devuelve 'opened' o 'failed'. Nunca lanza: el evento ya quedó registrado."""
        body = json.dumps(payload, separators=(",", ":")).encode()
        timestamp = str(int(time.time()))
        try:
            response = httpx.post(
                url,
                content=body,
                timeout=self._timeout,
                headers={
                    "Content-Type": "application/json",
                    "X-Portero-Timestamp": timestamp,
                    "X-Portero-Signature": sign(secret, timestamp, body),
                },
            )
        except httpx.HTTPError:
            return "failed"
        return "opened" if response.is_success else "failed"
