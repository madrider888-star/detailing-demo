"""Mock-провайдер для разработки и тестов: не ходит в сеть, результат детерминирован."""

from __future__ import annotations

import asyncio
from typing import ClassVar

from PIL import ImageDraw

from app.core.enums import Operation
from app.services.image_editing.base import (
    EditRequest,
    EditResult,
    ImageEditingProvider,
    ProviderError,
    ProviderUnavailableError,
)
from app.utils.images import encode_png, open_image


class MockImageProvider(ImageEditingProvider):
    """Возвращает исходное фото с пометкой «MOCK».

    Параметры позволяют моделировать сбои: `fail_times` первых вызовов падают с
    повторяемой ошибкой, `permanent_error` — падает всегда.
    """

    name: ClassVar[str] = "mock"
    supported_operations: ClassVar[frozenset[Operation]] = frozenset(Operation)

    def __init__(
        self,
        *,
        delay: float = 0.0,
        fail_times: int = 0,
        permanent_error: ProviderError | None = None,
    ) -> None:
        self.delay = delay
        self.fail_times = fail_times
        self.permanent_error = permanent_error
        self.calls = 0

    async def _edit(self, request: EditRequest) -> EditResult:
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.permanent_error is not None:
            raise self.permanent_error
        if self.calls <= self.fail_times:
            raise ProviderUnavailableError(f"mock transient failure #{self.calls}")

        image = open_image(request.image).convert("RGB")
        draw = ImageDraw.Draw(image)
        label = f"MOCK · {request.operation.value}"
        pad = max(6, image.width // 150)
        bbox = draw.textbbox((0, 0), label)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.rectangle((pad, pad, pad * 3 + w, pad * 3 + h), fill=(20, 120, 60))
        draw.text((pad * 2, pad * 2), label, fill=(255, 255, 255))
        return EditResult(
            image=encode_png(image),
            mime_type="image/png",
            provider=self.name,
            metadata={"mock": True, "references": len(request.references)},
        )
