"""Структурированные логи (structlog) с маскировкой секретов."""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import Iterable, MutableMapping
from typing import Any

import structlog

_SENSITIVE_KEYS = re.compile(r"(token|secret|password|api[_-]?key|authorization)", re.IGNORECASE)
# Telegram bot token: 123456:ABC-...
_BOT_TOKEN_RE = re.compile(r"(?<!\d)\d{6,12}:[A-Za-z0-9_-]{30,}")
_BEARER_RE = re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]+", re.IGNORECASE)
_OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b")

MASK = "***"


class SecretMasker:
    def __init__(self, secrets: Iterable[str] = ()) -> None:
        self._secrets = sorted({s for s in secrets if s}, key=len, reverse=True)

    def mask_text(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, MASK)
        text = _BOT_TOKEN_RE.sub(MASK, text)
        text = _OPENAI_KEY_RE.sub(MASK, text)
        return _BEARER_RE.sub(r"\1" + MASK, text)

    def mask_value(self, key: str, value: Any) -> Any:
        if _SENSITIVE_KEYS.search(key) and value not in (None, "", False):
            return MASK
        if isinstance(value, str):
            return self.mask_text(value)
        if isinstance(value, dict):
            return {k: self.mask_value(str(k), v) for k, v in value.items()}
        return value

    def structlog_processor(
        self, _logger: Any, _method: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        for key in list(event_dict):
            event_dict[key] = self.mask_value(key, event_dict[key])
        return event_dict


class _MaskingFilter(logging.Filter):
    """Маскирует секреты в записях стандартного logging (aiogram, httpx, arq)."""

    def __init__(self, masker: SecretMasker) -> None:
        super().__init__()
        self._masker = masker

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, dict):
            return True  # событие structlog — уже замаскировано процессором
        record.msg = self._masker.mask_text(record.getMessage())
        record.args = None
        return True


def configure_logging(level: str = "INFO", fmt: str = "json", secrets: Iterable[str] = ()) -> None:
    masker = SecretMasker(secrets)
    renderer: Any = (
        structlog.processors.JSONRenderer(ensure_ascii=False)
        if fmt == "json"
        else structlog.dev.ConsoleRenderer()
    )
    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        masker.structlog_processor,
    ]
    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(_MaskingFilter(masker))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # ARQ и uvicorn ставят собственные обработчики — переводим их на общий JSON-вывод.
    for name in ("arq", "uvicorn", "uvicorn.error", "uvicorn.access", "aiogram"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    # httpx пишет URL запросов на INFO — оставляем только предупреждения.
    for noisy in ("httpx", "httpcore", "botocore", "boto3", "urllib3", "aiobotocore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[no-any-return]
