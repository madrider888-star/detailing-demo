"""Локальный OpenCV-процессор номерных табличек как `ImageEditingProvider`."""

from __future__ import annotations

import asyncio
from typing import ClassVar

from app.core.enums import Operation
from app.services.image_editing.base import EditRequest, EditResult, ImageEditingProvider
from app.services.plate_replacement.service import PlateReplacer
from app.utils.images import bgr_to_pil, encode_png, open_image, pil_to_bgr


class OpenCVPlateProvider(ImageEditingProvider):
    name: ClassVar[str] = "opencv"
    supported_operations: ClassVar[frozenset[Operation]] = frozenset({Operation.PLATE})

    def __init__(self, replacer: PlateReplacer) -> None:
        self.replacer = replacer

    async def _edit(self, request: EditRequest) -> EditResult:
        def _run() -> EditResult:
            image = pil_to_bgr(open_image(request.image))
            outcome = self.replacer.replace(image)
            metadata = {
                "confidence": round(outcome.confidence, 3),
                "candidates": outcome.candidates,
                **outcome.metadata,
            }
            if not outcome.replaced:
                return EditResult(
                    image=request.image,
                    mime_type=request.mime_type,
                    provider=self.name,
                    needs_review=True,
                    review_reason="plate_low_confidence",
                    metadata=metadata,
                )
            return EditResult(
                image=encode_png(bgr_to_pil(outcome.image)),
                mime_type="image/png",
                provider=self.name,
                metadata=metadata,
            )

        # CPU-задача — в отдельном потоке, чтобы не блокировать event loop воркера.
        return await asyncio.to_thread(_run)
