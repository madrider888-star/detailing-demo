"""Настройки онлайн-консультанта. Все секреты читаются только из окружения / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _split_csv(value: object) -> object:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["dev", "prod", "test"] = "dev"
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    # Магазин и персона консультанта
    shop_name: str = "ECODRIVE AUTO"
    shop_site: str = "https://ecodrive.in.ua"
    bot_name: str = "Олена"
    knowledge_path: Path = PROJECT_ROOT / "knowledge"

    # OpenAI (Responses API)
    openai_api_key: SecretStr = SecretStr("")
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5.4"
    openai_reasoning_effort: Literal["minimal", "low", "medium", "high"] = "low"
    openai_timeout_seconds: float = 60.0
    max_output_tokens: int = 700
    max_tool_rounds: int = 5  # сколько раз подряд модель может вызывать инструменты
    history_messages: int = 30  # сколько последних сообщений диалога отдавать модели

    # KeyCRM: заказы, накладные, заявки менеджерам
    keycrm_api_key: SecretStr = SecretStr("")
    keycrm_base_url: str = "https://openapi.keycrm.app/v1"
    keycrm_pipeline_id: int | None = None  # воронка для обращений из чата (пусто — первая)
    keycrm_source_id: int | None = None  # источник заявки в KeyCRM (пусто — не передаём)

    # Нова Пошта: ключ для отслеживания не обязателен
    novaposhta_api_key: SecretStr = SecretStr("")

    # Каталог CS-Cart: с ключом — через REST API, без ключа — разбор страницы поиска
    cscart_base_url: str = "https://ecodrive.in.ua"
    cscart_api_email: str = ""
    cscart_api_key: SecretStr = SecretStr("")

    # Telegram менеджеров: отдельный бот (не фото-бот) и id группы менеджеров
    telegram_bot_token: SecretStr = SecretStr("")
    telegram_managers_chat_id: int | None = None
    telegram_polling: bool = True

    # Веб
    public_base_url: str = ""  # напр. https://chat.ecodrive.in.ua; пусто — берём из запроса
    allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["https://ecodrive.in.ua", "https://www.ecodrive.in.ua"]
    )
    rate_limit_per_minute: int = 20  # сообщений в минуту с одного IP или сессии
    max_message_chars: int = 2000
    database_url: str = f"sqlite+aiosqlite:///{PROJECT_ROOT / 'var' / 'support.db'}"
    api_host: str = "0.0.0.0"  # noqa: S104 — слушаем внутри контейнера
    api_port: int = 8090

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_csv(cls, value: object) -> object:
        return _split_csv(value)

    @field_validator(
        "openai_api_key",
        "keycrm_api_key",
        "novaposhta_api_key",
        "cscart_api_key",
        "telegram_bot_token",
        mode="before",
    )
    @classmethod
    def _clean_secret(cls, value: object) -> object:
        # Ключ, вставленный в консоль, может прийти с пробелами, кавычками или
        # служебными символами вставки (ESC[200~ … ESC[201~).
        if isinstance(value, str):
            value = value.replace("\x1b[200~", "").replace("\x1b[201~", "")
            value = value.strip().strip("\"'").strip()
        return value

    @field_validator(
        "keycrm_pipeline_id", "keycrm_source_id", "telegram_managers_chat_id", mode="before"
    )
    @classmethod
    def _empty_to_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("knowledge_path", mode="after")
    @classmethod
    def _resolve_relative(cls, value: Path) -> Path:
        return value if value.is_absolute() else PROJECT_ROOT / value

    def secret_values(self) -> list[str]:
        """Значения секретов — для маскировки в логах."""
        secrets = [
            self.openai_api_key,
            self.keycrm_api_key,
            self.novaposhta_api_key,
            self.cscart_api_key,
            self.telegram_bot_token,
        ]
        values = [s.get_secret_value() for s in secrets if s.get_secret_value()]
        if "@" in self.database_url and ":" in self.database_url.split("@")[0]:
            password = self.database_url.split("@")[0].rsplit(":", 1)[-1]
            if password:
                values.append(password)
        return [v for v in values if len(v) >= 4]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
