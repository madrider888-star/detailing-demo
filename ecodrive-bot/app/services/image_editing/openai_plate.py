"""Замена номера через OpenAI с жёсткой защитой остального кадра.

1. OpenCV находит номер (те же детектор и порог, что у локального процессора).
2. OpenAI получает фото, фирменный макет и маску: рисовать можно только около номера.
3. Из ответа берётся только эта область (с мягким краем), всё остальное — пиксели
   оригинала. Машина не меняется, даже если модель что-то «додумала» вне маски.
4. Если OpenAI недоступен или отклонил запрос, номер заменяется локально (OpenCV),
   чтобы сотрудник всё равно получил результат.
"""

from __future__ import annotations

import asyncio
import dataclasses
from typing import ClassVar

import cv2
import numpy as np
from PIL import Image

from app.core.enums import Operation
from app.core.logging import get_logger
from app.services.export.c2pa import embed_c2pa_png, extract_c2pa
from app.services.image_editing.base import (
    EditRequest,
    EditResult,
    ImageEditingProvider,
    ProviderConfigError,
    ProviderError,
    ReferenceImage,
)
from app.services.image_editing.openai_provider import OpenAIImageEditProvider
from app.services.image_editing.opencv_plate import OpenCVPlateProvider
from app.services.plate_replacement.geometry import expand_quad
from app.services.plate_replacement.overlay import fitted_quad
from app.services.plate_replacement.service import PlateReplacer
from app.utils.images import bgr_to_pil, encode_png, open_image, pil_to_bgr
from app.utils.types import ImageArray, Quad

log = get_logger(__name__)


def edit_region(corners: Quad, template_aspect: float, height_ratio: float) -> Quad:
    """Область, где модели разрешено рисовать: старый номер + новая табличка с запасом."""
    target = fitted_quad(corners, template_aspect, height_ratio=height_ratio)
    plate = expand_quad(corners.astype(np.float32), 0.08, 0.2)
    points = np.vstack([expand_quad(target, 0.25, 0.45), plate]).astype(np.float32)
    hull = cv2.convexHull(points)
    return hull.reshape(-1, 2).astype(np.float32)


def region_masks(shape: tuple[int, int], region: Quad) -> tuple[ImageArray, ImageArray]:
    """Маска для OpenAI (RGBA, прозрачно = рисовать) и мягкая маска для вклейки (0..1)."""
    h, w = shape
    hard = np.zeros((h, w), np.uint8)
    cv2.fillConvexPoly(hard, np.round(region).astype(np.int32), 255)
    api_mask = np.full((h, w, 4), 255, np.uint8)
    api_mask[..., 3] = 255 - hard
    span = float(np.ptp(region[:, 1])) if len(region) else 10.0
    soft = cv2.GaussianBlur(
        cv2.erode(hard, np.ones((3, 3), np.uint8)).astype(np.float32) / 255.0,
        (0, 0),
        max(1.5, span * 0.04),
    )
    return api_mask, soft


class OpenAIPlateProvider(ImageEditingProvider):
    name: ClassVar[str] = "openai"
    supported_operations: ClassVar[frozenset[Operation]] = frozenset({Operation.PLATE})

    def __init__(
        self,
        editor: OpenAIImageEditProvider,
        replacer: PlateReplacer,
        template_png: bytes,
    ) -> None:
        self.editor = editor
        self.replacer = replacer
        self.template_png = template_png
        self.fallback = OpenCVPlateProvider(replacer)
        tpl = replacer.template
        self.template_aspect = tpl.shape[1] / tpl.shape[0]

    async def aclose(self) -> None:
        await self.editor.aclose()

    async def _edit(self, request: EditRequest) -> EditResult:
        original = open_image(request.image).convert("RGB")
        bgr = pil_to_bgr(original)
        detections = await asyncio.to_thread(self.replacer.detector.detect, bgr)
        best = detections[0] if detections else None
        if best is None or best.confidence < self.replacer.threshold:
            # Без уверенно найденного номера модель может «нарисовать» его где угодно.
            return await self.fallback.edit(request)

        region = edit_region(best.corners, self.template_aspect, self.replacer.height_ratio)
        api_mask, soft = region_masks(bgr.shape[:2], region)
        ai_request = dataclasses.replace(
            request,
            mask=encode_png(Image.fromarray(api_mask, "RGBA")),
            references=(ReferenceImage(self.template_png, "image/png", "plate"),),
        )
        try:
            result = await self.editor.edit(ai_request)
        except ProviderConfigError:
            raise
        except ProviderError as exc:
            log.warning("plate.openai_fallback", job_id=request.job_id, error=type(exc).__name__)
            local = await self.fallback.edit(request)
            local.metadata["fallback"] = f"opencv ({type(exc).__name__})"
            return local

        def _composite() -> bytes:
            generated = pil_to_bgr(open_image(result.image).convert("RGB"))
            if generated.shape[:2] != bgr.shape[:2]:
                generated = cv2.resize(
                    generated, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_LANCZOS4
                )
            a = soft[..., None]
            merged = generated.astype(np.float32) * a + bgr.astype(np.float32) * (1.0 - a)
            out = encode_png(bgr_to_pil(np.clip(merged + 0.5, 0, 255).astype(np.uint8)))
            provenance = extract_c2pa(result.image)
            return embed_c2pa_png(out, provenance) if provenance else out

        data = await asyncio.to_thread(_composite)
        return EditResult(
            image=data,
            mime_type="image/png",
            provider=self.name,
            metadata={
                **result.metadata,
                "confidence": round(best.confidence, 3),
                "masked": True,
            },
        )
