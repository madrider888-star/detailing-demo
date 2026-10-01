"""Единый интерфейс поставщиков обработки изображений.

Telegram-бот и воркер знают только об `ImageEditingProvider`: замена поставщика
(mock → OpenAI → другой API → локальная модель) не требует правок в боте.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

from app.core.enums import Operation
from app.prompts.builder import Prompt


@dataclass(frozen=True)
class ReferenceImage:
    data: bytes
    mime_type: str
    role: str  # "wheel" | "background" | "plate"


@dataclass(frozen=True)
class EditRequest:
    job_id: int
    operation: Operation
    image: bytes
    mime_type: str
    parameters: dict[str, Any]
    prompt: Prompt
    references: tuple[ReferenceImage, ...] = ()


@dataclass
class EditResult:
    image: bytes
    mime_type: str
    provider: str
    needs_review: bool = False
    review_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderError(Exception):
    """Ошибка поставщика. `retryable` — имеет ли смысл повторить запрос."""

    retryable: bool = False
    user_message: str = (
        "Сервис обработки вернул ошибку. Попробуйте позже или сообщите администратору."
    )

    def __init__(self, message: str, *, retryable: bool | None = None) -> None:
        super().__init__(message)
        if retryable is not None:
            self.retryable = retryable


class ProviderTimeoutError(ProviderError):
    retryable = True
    user_message = "Сервис обработки не ответил вовремя. Попробуйте ещё раз чуть позже."


class ProviderUnavailableError(ProviderError):
    retryable = True
    user_message = "Сервис обработки временно недоступен. Попробуйте ещё раз чуть позже."


class ProviderRejectedError(ProviderError):
    retryable = False
    user_message = (
        "Сервис обработки отклонил изображение. Попробуйте другую фотографию "
        "или передайте задание оператору."
    )


class ProviderConfigError(ProviderError):
    retryable = False
    user_message = "Сервис обработки не настроен. Сообщите администратору."


class UnsupportedOperationError(ProviderError):
    retryable = False
    user_message = "Эта операция пока не поддерживается выбранным сервисом обработки."


class ImageEditingProvider(ABC):
    name: ClassVar[str]
    supported_operations: ClassVar[frozenset[Operation]]

    def supports(self, operation: Operation) -> bool:
        return operation in self.supported_operations

    async def edit(self, request: EditRequest) -> EditResult:
        if not self.supports(request.operation):
            raise UnsupportedOperationError(f"{self.name} does not support {request.operation}")
        return await self._edit(request)

    @abstractmethod
    async def _edit(self, request: EditRequest) -> EditResult: ...

    async def aclose(self) -> None:  # noqa: B027 — необязательный хук
        """Освободить сетевые ресурсы."""
