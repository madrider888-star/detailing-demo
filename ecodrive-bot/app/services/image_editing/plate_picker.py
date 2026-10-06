"""Выбор номера среди кандидатов детектора с помощью vision-модели OpenAI.

Контурный детектор находит «похожие на номер» прямоугольники, но не понимает сцену:
табличка на бордюре, вывеска или наклейка могут набрать больше баллов, чем настоящий
номер автомобиля. Модель видит фото с пронумерованными рамками и отвечает, какая из
них — номерной знак, закреплённый на машине (или что такой рамки нет).
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any

import cv2
import httpx
import numpy as np

from app.core.logging import get_logger
from app.services.image_editing.base import (
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.services.image_editing.openai_provider import OpenAIImageEditProvider
from app.services.plate_replacement.detector import PlateDetection
from app.utils.retry import call_with_retry
from app.utils.types import ImageArray

log = get_logger(__name__)

PREVIEW_MAX_SIDE = 1600
COLORS = [(0, 0, 255), (0, 200, 0), (255, 0, 0), (0, 200, 255), (255, 0, 255)]  # BGR

PROMPT = (
    "This is a photo of a car. Numbered coloured boxes mark candidate regions found by a "
    "detector. Which box contains the car's own licence plate — the number plate mounted "
    "on the front or rear bumper of the main car in the photo? It may be from any country, "
    "any colour (white, yellow, black...), or a dealer/placeholder plate with a logo instead "
    "of a number. Boxes on road signs, kerbs, buildings, windows, lights, stickers, other "
    "cars or any object that is not the main car's plate do NOT count. "
    'Answer with JSON only: {"plate": N} where N is the box number, '
    'or {"plate": 0} if no box contains the main car\'s licence plate.'
)


def draw_candidates(image: ImageArray, candidates: list[PlateDetection]) -> bytes:
    """JPEG-превью с пронумерованными рамками кандидатов (номер — над рамкой)."""
    h, w = image.shape[:2]
    scale = min(1.0, PREVIEW_MAX_SIDE / max(h, w))
    preview = (
        cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
        if scale < 1.0
        else image.copy()
    )
    thickness = max(2, round(max(preview.shape[:2]) / 500))
    font_scale = max(0.6, max(preview.shape[:2]) / 1400)
    for idx, det in enumerate(candidates, start=1):
        color = COLORS[(idx - 1) % len(COLORS)]
        pts = np.round(det.corners * scale).astype(np.int32)
        cv2.polylines(preview, [pts], True, color, thickness, cv2.LINE_AA)
        label = str(idx)
        (tw, th), base = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
        x = int(pts[:, 0].min())
        y = int(pts[:, 1].min()) - thickness - 2
        if y - th - base < 0:  # нет места сверху — подпись под рамкой
            y = int(pts[:, 1].max()) + th + thickness + 2
        cv2.rectangle(preview, (x, y - th - base), (x + tw + 6, y + base // 2), color, -1)
        cv2.putText(
            preview,
            label,
            (x + 3, y - base // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    ok, buf = cv2.imencode(".jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise ProviderError("failed to encode preview")
    return buf.tobytes()


def parse_choice(text: str, count: int) -> int | None:
    """Ответ модели → индекс кандидата (с 0) или None («номера среди рамок нет»)."""
    match = re.search(r"\{[^{}]*\}", text)
    if match is None:
        raise ProviderError("plate picker: no JSON in answer")
    try:
        value = int(json.loads(match.group(0))["plate"])
    except (ValueError, KeyError, TypeError) as exc:
        raise ProviderError("plate picker: malformed answer") from exc
    if value == 0:
        return None
    if not 1 <= value <= count:
        raise ProviderError("plate picker: box number out of range")
    return value - 1


def _output_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in payload.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") == "output_text":
                parts.append(str(content.get("text", "")))
    if not parts:
        raise ProviderError("plate picker: empty answer", retryable=True)
    return "".join(parts)


class OpenAIPlatePicker:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-5",
        timeout: float = 90.0,
        max_retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
        retry_initial_delay: float = 2.0,
    ) -> None:
        self.model = model
        self.max_retries = max_retries
        self.retry_initial_delay = retry_initial_delay
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(timeout, connect=15.0),
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def pick(self, image: ImageArray, candidates: list[PlateDetection]) -> int | None:
        """Индекс настоящего номера среди `candidates` или None, если его там нет."""
        preview = base64.b64encode(draw_candidates(image, candidates)).decode()
        body = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": PROMPT},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{preview}",
                            "detail": "high",
                        },
                    ],
                }
            ],
        }

        async def _call() -> str:
            try:
                response = await self._client.post("/responses", json=body)
            except httpx.TimeoutException as exc:
                raise ProviderTimeoutError("plate picker timed out") from exc
            except httpx.TransportError as exc:
                raise ProviderUnavailableError(f"transport error: {type(exc).__name__}") from exc
            if response.status_code >= 400:
                raise OpenAIImageEditProvider._map_error(response)
            try:
                payload = response.json()
            except ValueError as exc:
                raise ProviderError("plate picker: malformed response", retryable=True) from exc
            return _output_text(payload)

        text = await call_with_retry(
            _call, attempts=self.max_retries, initial_delay=self.retry_initial_delay
        )
        choice = parse_choice(text, len(candidates))
        log.info("plate.picker", candidates=len(candidates), choice=choice)
        return choice
