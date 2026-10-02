"""Настройки приложения. Все секреты читаются только из окружения / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from app.core.enums import Operation

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _split_csv(value: object) -> object:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, int):
        return [value]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["dev", "prod", "test"] = "dev"
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    # Telegram
    bot_token: SecretStr = SecretStr("")
    admin_telegram_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)
    allowed_telegram_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)

    # Инфраструктура
    database_url: str = "postgresql+asyncpg://ecodrive:ecodrive@localhost:5432/ecodrive"
    redis_url: str = "redis://localhost:6379/0"

    storage_backend: Literal["s3", "local"] = "local"
    s3_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_bucket: str = "ecodrive-media"
    s3_access_key: SecretStr = SecretStr("")
    s3_secret_key: SecretStr = SecretStr("")
    local_storage_path: Path = PROJECT_ROOT / "var" / "storage"

    # Провайдеры
    image_provider: Literal["mock", "openai"] = "mock"
    plate_provider: Literal["opencv", "openai", "mock"] = "opencv"
    # auto — брать рисунок модели, если логотип совпал с макетом; lighting — только свет
    plate_ai_mode: Literal["auto", "lighting"] = "auto"
    plate_ai_min_similarity: float = Field(default=0.75, ge=0.0, le=1.0)
    openai_api_key: SecretStr = SecretStr("")
    openai_base_url: str = "https://api.openai.com/v1"
    openai_image_model: str = "gpt-image-2"
    openai_image_quality: str = "high"
    openai_input_fidelity: str | None = "high"  # только для gpt-image-1.x
    openai_image_max_edge: int = Field(default=2560, ge=1024, le=3840)
    provider_timeout_seconds: float = 180.0
    provider_max_retries: int = 3

    # Номера
    branded_plate_path: Path = PROJECT_ROOT / "assets" / "branded_plate" / "ecodrive_plate.png"
    backgrounds_path: Path = PROJECT_ROOT / "assets" / "backgrounds"
    plate_confidence_threshold: float = 0.55
    # Высота фирменной таблички относительно высоты номера (если её форма не как у номера)
    plate_template_height_ratio: float = Field(default=1.5, ge=0.8, le=2.5)
    plate_detector_model_path: Path | None = None

    # Лимиты
    max_upload_bytes: int = 20 * 1024 * 1024
    max_image_pixels: int = 60_000_000
    min_image_side: int = 320
    max_active_jobs_per_user: int = 2

    # Экспорт
    export_max_side: int = 2560
    export_jpeg_quality: int = Field(default=92, ge=90, le=95)
    export_min_jpeg_quality: int = Field(default=90, ge=90, le=95)
    export_max_bytes: int = 8 * 1024 * 1024
    visualization_label_enabled: bool = True
    visualization_label_text: str = "Візуалізація"
    visualization_label_operations: Annotated[list[Operation], NoDecode] = Field(
        default_factory=lambda: [Operation.BACKGROUND, Operation.WHEELS, Operation.INTERIOR_COLOR]
    )
    font_path: Path = PROJECT_ROOT / "assets" / "fonts" / "DejaVuSans.ttf"

    # API
    api_host: str = "0.0.0.0"  # noqa: S104 — слушаем внутри контейнера
    api_port: int = 8080

    @field_validator(
        "admin_telegram_ids",
        "allowed_telegram_ids",
        "visualization_label_operations",
        mode="before",
    )
    @classmethod
    def _parse_csv(cls, value: object) -> object:
        return _split_csv(value)

    @field_validator("plate_detector_model_path", "s3_endpoint_url", mode="before")
    @classmethod
    def _empty_to_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("branded_plate_path", "backgrounds_path", "font_path", mode="after")
    @classmethod
    def _resolve_relative(cls, value: Path) -> Path:
        return value if value.is_absolute() else PROJECT_ROOT / value

    def secret_values(self) -> list[str]:
        """Значения секретов — для маскировки в логах."""
        secrets = [self.bot_token, self.openai_api_key, self.s3_access_key, self.s3_secret_key]
        values = [s.get_secret_value() for s in secrets if s.get_secret_value()]
        if "@" in self.database_url and ":" in self.database_url.split("@")[0]:
            password = self.database_url.split("@")[0].rsplit(":", 1)[-1]
            if password:
                values.append(password)
        return [v for v in values if len(v) >= 4]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
