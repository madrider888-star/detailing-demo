"""Замена номера с участием OpenAI — без искажения логотипа и без потери резкости.

Схема:
1. Табличка ставится программно (OpenCV): точный макет, правильные пропорции и
   перспектива, старый номер закрашен.
2. В OpenAI уходит только квадратный фрагмент вокруг номера в высоком разрешении,
   с маской-полосой вокруг таблички: модель «фотографирует» табличку в сцене —
   свет, блики, кант, тень.
3. Из ответа берётся **только освещение** (сглаженная яркость): оно переносится на
   точный макет и на кузов вокруг (тень). Пиксели логотипа и форма таблички всегда
   из макета — модель не может их перерисовать, размыть или обрезать.
4. Всё вне фрагмента — пиксели оригинала. Если OpenAI недоступен — результат шага 1.
"""

from __future__ import annotations

import asyncio
import dataclasses
from dataclasses import dataclass
from typing import ClassVar

import cv2
import numpy as np
from PIL import Image

from app.core.enums import Operation
from app.core.logging import get_logger
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
from app.services.plate_replacement.geometry import expand_quad, quad_size
from app.services.plate_replacement.overlay import fitted_quad
from app.services.plate_replacement.service import PlateReplacer
from app.utils.images import bgr_to_pil, encode_png, open_image, pil_to_bgr
from app.utils.types import ImageArray, Quad

log = get_logger(__name__)

CROP_SCALE = 2.6  # сторона фрагмента относительно ширины таблички
MIN_LOGO_SIMILARITY = 0.75  # насколько табличка модели должна совпадать с макетом
FACE_GAIN = (0.65, 1.3)  # насколько ИИ может затемнить/осветлить саму табличку
BAND_GAIN = (0.55, 1.15)  # и кузов вокруг неё (тень, отсвет)


@dataclass(frozen=True)
class Crop:
    x0: int
    y0: int
    x1: int
    y1: int

    def take(self, image: ImageArray) -> ImageArray:
        return image[self.y0 : self.y1, self.x0 : self.x1]

    def shift(self, quad: Quad) -> Quad:
        return (quad - np.array([self.x0, self.y0], dtype=np.float32)).astype(np.float32)


def crop_around(quad: Quad, shape: tuple[int, int]) -> Crop:
    """Квадратный фрагмент вокруг таблички (не выходит за кадр)."""
    h, w = shape
    width, _ = quad_size(quad)
    side = int(min(max(width * CROP_SCALE, 256), w, h))
    cx, cy = quad.mean(axis=0)
    x0 = int(np.clip(round(cx - side / 2), 0, w - side))
    y0 = int(np.clip(round(cy - side / 2), 0, h - side))
    return Crop(x0, y0, x0 + side, y0 + side)


def edit_region(target: Quad) -> Quad:
    """Полоса вокруг таблички, где модель рисует кант, блики и тень."""
    return expand_quad(target, 0.14, 0.4)


def _poly_mask(shape: tuple[int, int], quad: Quad) -> ImageArray:
    mask = np.zeros(shape, np.uint8)
    cv2.fillConvexPoly(mask, np.round(quad).astype(np.int32), 255)
    return mask


def _lum(image: ImageArray, sigma: float) -> ImageArray:
    gray = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    return cv2.GaussianBlur(gray, (0, 0), sigma) + 1.0


def logo_similarity(a: ImageArray, b: ImageArray, quad: Quad) -> float:
    """Совпадение рисунка таблички (нормированная корреляция в её плоскости)."""
    from app.services.plate_replacement.detector import rectify

    width, height = quad_size(quad)
    size = (max(32, round(width)), max(16, round(height)))
    ga = cv2.cvtColor(rectify(a, quad, size), cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(rectify(b, quad, size), cv2.COLOR_BGR2GRAY).astype(np.float32)
    ga, gb = ga - ga.mean(), gb - gb.mean()
    denom = float(np.sqrt((ga * ga).sum() * (gb * gb).sum())) + 1e-6
    return float((ga * gb).sum() / denom)


def blend_generated(
    placed: ImageArray, generated: ImageArray, region: Quad, plate_h: float
) -> ImageArray:
    """Пиксели модели внутри полосы вокруг таблички, мягкий край, снаружи — без изменений."""
    hard = _poly_mask(placed.shape[:2], region).astype(np.float32) / 255.0
    soft = cv2.GaussianBlur(
        cv2.erode(hard, np.ones((3, 3), np.uint8)), (0, 0), max(1.5, plate_h * 0.06)
    )
    a = soft[..., None]
    out = generated.astype(np.float32) * a + placed.astype(np.float32) * (1.0 - a)
    result: ImageArray = np.clip(out + 0.5, 0, 255).astype(np.uint8)
    return result


def transfer_lighting(
    placed: ImageArray,
    generated: ImageArray,
    plate_quad: Quad,
    region: Quad,
) -> ImageArray:
    """Переносит освещение из ответа модели на точный результат (в координатах фрагмента)."""
    shape = placed.shape[:2]
    _, plate_h = quad_size(plate_quad)
    # Сильное сглаживание: переносим только свет (градиенты, тень), а не детали —
    # иначе неточно нарисованный моделью логотип «проступает» ореолом.
    sigma_face = max(3.0, plate_h * 0.35)
    sigma_band = max(3.0, plate_h * 0.3)
    gain_face = _lum(generated, sigma_face) / _lum(placed, sigma_face)
    gain_band = _lum(generated, sigma_band) / _lum(placed, sigma_band)

    face: ImageArray = cv2.GaussianBlur(
        _poly_mask(shape, plate_quad).astype(np.float32) / 255.0, (0, 0), 1.0
    )
    band: ImageArray = cv2.GaussianBlur(
        _poly_mask(shape, region).astype(np.float32) / 255.0, (0, 0), max(2.0, plate_h * 0.08)
    )

    g_face = np.clip(gain_face, *FACE_GAIN)
    g_band = np.clip(gain_band, *BAND_GAIN)
    total_gain = face * g_face + (1.0 - face) * (band * g_band + (1.0 - band))
    out = placed.astype(np.float32) * total_gain[..., None]
    result: ImageArray = np.clip(out + 0.5, 0, 255).astype(np.uint8)
    return result


class OpenAIPlateProvider(ImageEditingProvider):
    name: ClassVar[str] = "openai"
    supported_operations: ClassVar[frozenset[Operation]] = frozenset({Operation.PLATE})

    def __init__(
        self,
        editor: OpenAIImageEditProvider,
        replacer: PlateReplacer,
        template_png: bytes,
        *,
        mode: str = "lighting",
        min_similarity: float = MIN_LOGO_SIMILARITY,
    ) -> None:
        self.mode = mode
        self.min_similarity = min_similarity
        self.editor = editor
        self.replacer = replacer
        self.template_png = template_png
        self.fallback = OpenCVPlateProvider(replacer)
        tpl = replacer.template
        self.template_aspect = tpl.shape[1] / tpl.shape[0]

    async def aclose(self) -> None:
        await self.editor.aclose()

    async def _edit(self, request: EditRequest) -> EditResult:
        bgr = pil_to_bgr(open_image(request.image).convert("RGB"))
        # 1. Точная программная постановка таблички.
        placed_outcome = await asyncio.to_thread(self.replacer.replace, bgr)
        best = placed_outcome.detection
        if not placed_outcome.replaced or best is None:
            # Номер не найден уверенно — модель могла бы «нарисовать» его где угодно.
            return await self.fallback.edit(request)
        placed = placed_outcome.image
        local = EditResult(
            image=encode_png(bgr_to_pil(placed)),
            mime_type="image/png",
            provider="opencv",
            metadata={"confidence": round(best.confidence, 3)},
        )

        # 2. Фрагмент вокруг таблички + маска-полоса → OpenAI.
        target = fitted_quad(
            best.corners, self.template_aspect, height_ratio=self.replacer.height_ratio
        )
        crop = crop_around(target, placed.shape[:2])
        placed_crop = crop.take(placed).copy()
        target_c, region_c = crop.shift(target), crop.shift(edit_region(target))
        api_mask = np.full((*placed_crop.shape[:2], 4), 255, np.uint8)
        api_mask[..., 3] = 255 - _poly_mask(placed_crop.shape[:2], region_c)
        ai_request = dataclasses.replace(
            request,
            image=encode_png(bgr_to_pil(placed_crop)),
            mime_type="image/png",
            mask=encode_png(Image.fromarray(api_mask, "RGBA")),
            references=(ReferenceImage(self.template_png, "image/png", "plate"),),
        )
        try:
            result = await self.editor.edit(ai_request)
        except ProviderConfigError:
            raise
        except ProviderError as exc:
            log.warning("plate.openai_fallback", job_id=request.job_id, error=type(exc).__name__)
            local.metadata["fallback"] = f"opencv ({type(exc).__name__})"
            return local

        # 3. Если модель нарисовала табличку точно (логотип совпадает с макетом) —
        #    берём её пиксели; иначе — только освещение на точный макет.
        def _finish() -> tuple[bytes, str, float]:
            generated = pil_to_bgr(open_image(result.image).convert("RGB"))
            if generated.shape[:2] != placed_crop.shape[:2]:
                generated = cv2.resize(
                    generated,
                    (placed_crop.shape[1], placed_crop.shape[0]),
                    interpolation=cv2.INTER_AREA,
                )
            similarity = logo_similarity(generated, placed_crop, target_c)
            _, plate_h = quad_size(target_c)
            if self.mode == "auto" and similarity >= self.min_similarity:
                patch, used = (
                    blend_generated(placed_crop, generated, region_c, plate_h),
                    "generated",
                )
            else:
                patch, used = (
                    transfer_lighting(placed_crop, generated, target_c, region_c),
                    "lighting",
                )
            out = placed.copy()
            out[crop.y0 : crop.y1, crop.x0 : crop.x1] = patch
            return encode_png(bgr_to_pil(out)), used, similarity

        data, used, similarity = await asyncio.to_thread(_finish)
        return EditResult(
            image=data,
            mime_type="image/png",
            provider=self.name,
            metadata={
                **result.metadata,
                "confidence": round(best.confidence, 3),
                "mode": used,
                "logo_similarity": round(similarity, 3),
            },
        )
