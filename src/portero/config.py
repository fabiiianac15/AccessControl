"""Configuración leída del entorno (prefijo PORTERO_) o de un archivo .env."""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PORTERO_", env_file=".env", extra="ignore")

    data_dir: Path = Path("data")
    master_key: str | None = Field(
        default=None,
        description="Clave maestra en base64 (32 bytes). Si falta, se crea data_dir/secret.key.",
    )
    host: str = "127.0.0.1"
    port: int = 8000
    timezone: str = "America/Bogota"

    org_name: str = "Mi organización"
    privacy_contact: str = "Sin configurar (PORTERO_PRIVACY_CONTACT)"

    # Similitud coseno de SFace. Ver docs/evaluacion.md para la curva que justifica estos valores.
    match_threshold: float = 0.45
    match_margin: float = 0.05
    min_samples: int = 3
    max_samples: int = 8

    liveness_timeout_seconds: float = 15.0
    # Razón nariz-ojos (ver biometrics/liveness.py).
    liveness_turn_ratio: float = 0.28
    liveness_center_ratio: float = 0.14
    liveness_min_aspect: float = 0.65

    pin_max_failures: int = 5
    pin_lockout_seconds: int = 120
    pin_lockout_max_seconds: int = 3600

    retention_days: int = 180
    store_denied_photos: bool = False

    session_hours: int = 12
    max_frame_bytes: int = 3 * 1024 * 1024

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def db_path(self) -> Path:
        return self.data_dir / "portero.db"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    @property
    def photos_dir(self) -> Path:
        return self.data_dir / "photos"
