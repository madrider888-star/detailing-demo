"""Номер через OpenAI: маска, вклейка только области номера, запасной OpenCV."""

from __future__ import annotations

import base64
import io

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


def _magenta(size: tuple[int, int]) -> httpx.Response:
    buf = io.BytesIO()
    Image.new("RGB", size, (255, 0, 255)).save(buf, "PNG")
    return httpx.Response(
        200, json={"data": [{"b64_json": base64.b64encode(buf.getvalue()).decode()}]}
    )


async def test_openai_plate_edits_only_plate_region(settings: Settings) -> None:
    seen: dict[str, bool] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content
        seen["mask"] = b'name="mask"' in body
        seen["reference"] = b"reference_0_plate.png" in body
        seen["prompt"] = b"Do NOT change the plate" in body
        return _magenta((1536, 1024))  # модель «перекрасила» весь кадр

    scene, truth = make_scene()
    result = await _provider(settings, handler).edit(_request(to_jpeg_bytes(scene, 95)))
    assert seen == {"mask": True, "reference": True, "prompt": True}
    assert result.provider == "openai"
    out = pil_to_bgr(open_image(result.image))
    original = pil_to_bgr(open_image(to_jpeg_bytes(scene, 95)))
    center = truth.mean(axis=0).astype(int)
    # Внутри области номера — результат модели.
    assert tuple(out[center[1], center[0]]) == (255, 0, 255)
    # Вне её — пиксели оригинала, несмотря на то что модель изменила весь кадр.
    for x, y in [(100, 100), (300, 400), (1200, 800), (center[0], center[1] - 250)]:
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
        return _magenta((1024, 1024))

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
