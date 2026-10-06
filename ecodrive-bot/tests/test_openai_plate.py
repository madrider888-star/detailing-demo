"""Номер через OpenAI: маска, вклейка только области номера, запасной OpenCV."""

from __future__ import annotations

import base64
import io
import re

import cv2
import httpx
import numpy as np
from PIL import Image
from pydantic import SecretStr

from app.core.config import Settings
from app.core.enums import Operation
from app.prompts.builder import build_prompt
from app.services.image_editing.base import EditRequest
from app.services.image_editing.factory import build_plate_provider
from app.services.image_editing.openai_plate import OpenAIPlateProvider
from app.services.image_editing.openai_provider import OpenAIImageEditProvider
from app.services.plate_replacement.detector import rectify
from app.services.plate_replacement.overlay import fitted_quad
from app.utils.images import encode_png, open_image, pil_to_bgr
from tests.synthetic import make_scene, to_jpeg_bytes


def _provider(settings: Settings, handler: object) -> OpenAIPlateProvider:
    base = build_plate_provider(settings.model_copy(update={"plate_provider": "opencv"}))
    replacer = base.replacer  # type: ignore[attr-defined]
    editor = OpenAIImageEditProvider(
        api_key="sk-test-0123456789abcdef",
        base_url="https://example.test/v1",
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
        max_retries=2,
        retry_initial_delay=0.01,
    )
    return OpenAIPlateProvider(editor, replacer, settings.branded_plate_path.read_bytes())


def _request(image: bytes) -> EditRequest:
    return EditRequest(
        job_id=1,
        operation=Operation.PLATE,
        image=image,
        mime_type="image/jpeg",
        parameters={},
        prompt=build_prompt(Operation.PLATE, {}),
    )


def _solid(size: tuple[int, int], color: tuple[int, int, int]) -> httpx.Response:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return httpx.Response(
        200, json={"data": [{"b64_json": base64.b64encode(buf.getvalue()).decode()}]}
    )


async def test_openai_plate_keeps_exact_logo_and_rest_of_car(settings: Settings) -> None:
    seen: dict[str, bool] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content
        seen["mask"] = b'name="mask"' in body
        seen["reference"] = b"reference_0_plate.png" in body
        seen["prompt"] = b"Do NOT change the plate" in body
        seen["square_crop"] = re.search(rb'name="size"\r\n\r\n(\d+)x\1\r', body) is not None
        # Модель вернула «кашу»: однотонный серый вместо таблички.
        return _solid((1024, 1024), (90, 90, 90))

    scene, truth = make_scene()
    source = to_jpeg_bytes(scene, 95)
    provider = _provider(settings, handler)
    result = await provider.edit(_request(source))
    assert seen == {"mask": True, "reference": True, "prompt": True, "square_crop": True}
    assert result.provider == "openai"

    out = pil_to_bgr(open_image(result.image))
    original = pil_to_bgr(open_image(source))
    placed = provider.replacer.replace(original).image
    target = fitted_quad(truth, 732 / 290, height_ratio=provider.replacer.height_ratio)
    # Логотип и надписи — точно из макета: рисунок таблички совпадает с программной версией.
    a = cv2.cvtColor(rectify(out, target, (366, 145)), cv2.COLOR_BGR2GRAY).astype(float)
    b = cv2.cvtColor(rectify(placed, target, (366, 145)), cv2.COLOR_BGR2GRAY).astype(float)
    a, b = a - a.mean(), b - b.mean()
    assert (a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()) > 0.95
    # Вне фрагмента вокруг номера — пиксели оригинала.
    for x, y in [(60, 60), (1200, 60), (60, 800), (1220, 820)]:
        assert np.abs(out[y, x].astype(int) - original[y, x].astype(int)).max() <= 2


async def test_openai_plate_falls_back_to_opencv(settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": {"code": "overloaded"}})

    scene, _ = make_scene()
    result = await _provider(settings, handler).edit(_request(to_jpeg_bytes(scene)))
    assert result.provider == "opencv"
    assert not result.needs_review
    assert "fallback" in result.metadata


async def test_openai_plate_without_plate_needs_review(settings: Settings) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return _solid((1024, 1024), (255, 0, 255))

    blank = encode_png(Image.new("RGB", (900, 600), (120, 130, 140)))
    result = await _provider(settings, handler).edit(_request(blank))
    assert result.needs_review
    assert calls["n"] == 0  # без найденного номера в OpenAI не ходим


def test_factory_builds_openai_plate_provider(settings: Settings) -> None:
    provider = build_plate_provider(
        settings.model_copy(
            update={
                "plate_provider": "openai",
                "openai_api_key": SecretStr("sk-test-0123456789abcd"),
            }
        )
    )
    assert isinstance(provider, OpenAIPlateProvider)


async def test_accurate_model_output_is_used_directly(settings: Settings) -> None:
    """Модель «сфотографировала» табличку точно — берём её пиксели (с тенью и бликами)."""
    scene, _ = make_scene()
    source = to_jpeg_bytes(scene, 95)
    holder: dict[str, OpenAIPlateProvider] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        # Возвращаем присланный фрагмент, чуть «подсветив» его: рисунок таблички тот же.
        match = re.search(
            rb'filename="source.png"\r\nContent-Type: image/png\r\n\r\n', request.content
        )
        assert match is not None
        start = match.end()
        end = request.content.index(b"\r\n--", start)
        crop = Image.open(io.BytesIO(request.content[start:end])).convert("RGB")
        brighter = crop.point(lambda v: min(255, int(v * 1.1) + 3))
        buf = io.BytesIO()
        brighter.save(buf, "PNG")
        return httpx.Response(
            200, json={"data": [{"b64_json": base64.b64encode(buf.getvalue()).decode()}]}
        )

    holder["p"] = _provider(settings, handler)
    holder["p"].mode = "auto"
    result = await holder["p"].edit(_request(source))
    assert result.metadata["mode"] == "generated"
    assert result.metadata["logo_similarity"] >= 0.75


async def test_plate_ai_mode_lighting_never_uses_model_pixels(settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _solid((1024, 1024), (90, 90, 90))

    provider = _provider(settings, handler)
    provider.mode = "lighting"
    scene, _ = make_scene()
    result = await provider.edit(_request(to_jpeg_bytes(scene)))
    assert result.metadata["mode"] == "lighting"
