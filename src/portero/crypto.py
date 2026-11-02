"""Claves derivadas, cifrado en reposo y hashes de contraseñas, PIN y tokens.

El cifrado protege copias de la base de datos y respaldos filtrados. Quien controle el servidor
en ejecución tiene también la clave: este módulo no defiende de ese escenario.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

_hasher = PasswordHasher()
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


class Keyring:
    def __init__(self, master: bytes) -> None:
        if len(master) != 32:
            raise ValueError("La clave maestra debe tener 32 bytes")
        self._aead = AESGCM(self._derive(master, b"portero/aead/v1"))
        self.chain_key = self._derive(master, b"portero/chain/v1")
        self._pin_key = self._derive(master, b"portero/pin/v1")

    @staticmethod
    def _derive(master: bytes, info: bytes) -> bytes:
        return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(master)

    def encrypt(self, plaintext: bytes, context: str) -> bytes:
        """AES-256-GCM. `context` ata el cifrado a su dueño: mover un blob de fila lo invalida."""
        nonce = os.urandom(12)
        return nonce + self._aead.encrypt(nonce, plaintext, context.encode())

    def decrypt(self, blob: bytes, context: str) -> bytes:
        return self._aead.decrypt(blob[:12], blob[12:], context.encode())

    def pin_lookup(self, pin: str) -> str:
        return hmac.new(self._pin_key, pin.encode(), hashlib.sha256).hexdigest()


def load_keyring(key_b64: str | None, data_dir: Path) -> Keyring:
    if key_b64:
        return Keyring(base64.b64decode(key_b64))
    path = data_dir / "secret.key"
    if path.exists():
        return Keyring(base64.b64decode(path.read_text().strip()))
    data_dir.mkdir(parents=True, exist_ok=True)
    master = os.urandom(32)
    # O_EXCL evita pisar una clave creada por otro proceso; 0600 antes de escribir el contenido.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(base64.b64encode(master).decode())
    return Keyring(master)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored: str | None, password: str) -> bool:
    """Con `stored=None` verifica contra un hash falso para igualar el tiempo de respuesta."""
    try:
        ok = _hasher.verify(stored or _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return False
    return ok and stored is not None


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_pin() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"
