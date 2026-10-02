"""Провайдеры: переключение, OpenAI-совместимый API, ошибки и повторы."""

from __future__ import annotations

import base64
import io
import json
import logging

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from app.core.config import Settings
from app.core.enums import Operation
from app.core.logging import SecretMasker, configure_logging
from app.prompts.builder import build_prompt
from app.services.image_editing.base import (
    EditRequest,
    ProviderConfigError,
    ProviderError,
    ProviderRejectedError,
    ProviderUnavailableError,
    UnsupportedOperationError,
)
from app.services.image_editing.factory import build_registry
from app.services.image_editing.mock import MockImageProvider
from app.services.image_editing.openai_provider import OpenAIImageEditProvider, flexible_size
from app.services.image_editing.opencv_plate import OpenCVPlateProvider
from app.utils.canvas import fit_to_canvas, restore_from_canvas

API_KEY = "sk-test-SECRET-1234567890abcdef"


def _png(size: tuple[int, int], color: tuple[int, int, int] = (90, 90, 90)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    return buf.getvalue()


def _request(image: bytes, operation: Operation = Operation.BACKGROUND) -> EditRequest:
    params = {"background": "white_studio", "has_reference": False}
    return EditRequest(
        job_id=1,
        operation=operation,
        image=image,
        mime_type="image/png",
        parameters=params,
        prompt=build_prompt(Operation.BACKGROUND, params),
    )


def _provider(handler: httpx.MockTransport, retries: int = 3) -> OpenAIImageEditProvider:
    return OpenAIImageEditProvider(
        api_key=API_KEY,
        base_url="https://example.test/v1",
        transport=handler,
        max_retries=retries,
        retry_initial_delay=0.01,
    )


def _ok_response(size: tuple[int, int]) -> httpx.Response:
    b64 = base64.b64encode(_png(size, (200, 10, 10))).decode()
    return httpx.Response(200, json={"data": [{"b64_json": b64}]})


# ─────────────────────────── переключение ───────────────────────────


def test_registry_uses_mock_and_opencv_by_default(settings: Settings) -> None:
    registry = build_registry(settings)
    assert isinstance(registry.for_operation(Operation.BACKGROUND), MockImageProvider)
    assert isinstance(registry.for_operation(Operation.PLATE), OpenCVPlateProvider)


def test_registry_switches_to_openai(settings: Settings) -> None:
    switched = settings.model_copy(
        update={
            "image_provider": "openai",
            "openai_api_key": SecretStr(API_KEY),
            "plate_provider": "mock",
        }
    )
    registry = build_registry(switched)
    for op in (Operation.BACKGROUND, Operation.WHEELS, Operation.INTERIOR_COLOR):
        assert registry.name_for(op) == "openai"
    assert registry.name_for(Operation.PLATE) == "mock"


def test_openai_without_key_is_config_error(settings: Settings) -> None:
    with pytest.raises(ProviderConfigError):
        build_registry(settings.model_copy(update={"image_provider": "openai"}))


async def test_unsupported_operation(settings: Settings) -> None:
    plate_only = build_registry(settings).for_operation(Operation.PLATE)
    with pytest.raises(UnsupportedOperationError):
        await plate_only.edit(_request(_png((800, 600)), Operation.BACKGROUND))


# ─────────────────────────── OpenAI-совместимый API ───────────────────────────


async def test_openai_success_keeps_original_resolution() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["Authorization"]
        body = request.content.decode("latin-1")
        seen["model"] = "gpt-image-2" in body
        seen["size"] = "1792x1344" in body  # пропорции и почти исходное разрешение
        seen["no_fidelity"] = "input_fidelity" not in body  # gpt-image-2 отвечает 400
        seen["prompt_has_negative"] = "Do not change the vehicle make" in body
        return _ok_response((1792, 1344))

    provider = _provider(httpx.MockTransport(handler))
    result = await provider.edit(_request(_png((1800, 1350))))
    assert seen == {
        "auth": f"Bearer {API_KEY}",
        "model": True,
        "size": True,
        "no_fidelity": True,
        "prompt_has_negative": True,
    }
    assert Image.open(io.BytesIO(result.image)).size == (1800, 1350)
    assert result.provider == "openai"


async def test_legacy_model_uses_fixed_sizes_and_fidelity() -> None:
    seen: dict[str, bool] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode("latin-1")
        seen["size"] = "1536x1024" in body
        seen["fidelity"] = "input_fidelity" in body
        return _ok_response((1536, 1024))

    provider = OpenAIImageEditProvider(
        api_key=API_KEY,
        base_url="https://example.test/v1",
        model="gpt-image-1",
        transport=httpx.MockTransport(handler),
        retry_initial_delay=0.01,
    )
    result = await provider.edit(_request(_png((1800, 1350))))
    assert seen == {"size": True, "fidelity": True}
    assert Image.open(io.BytesIO(result.image)).size == (1800, 1350)


def test_flexible_size_rules() -> None:
    for src in [(1800, 1350), (2508, 1672), (700, 700), (4032, 3024), (300, 1200)]:
        w, h = flexible_size(*src, 2560)
        assert w % 16 == 0 and h % 16 == 0
        assert max(w, h) <= 2560
        assert max(w / h, h / w) <= 3.0
        assert 655_360 <= w * h <= 8_294_400


async def test_openai_retries_with_backoff_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503, json={"error": {"code": "overloaded"}})
        return _ok_response((1024, 1024))

    result = await _provider(httpx.MockTransport(handler)).edit(_request(_png((800, 800))))
    assert calls["n"] == 3
    assert result.image


async def test_openai_gives_up_after_max_retries() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ConnectTimeout("timeout", request=request)

    with pytest.raises(ProviderError) as exc_info:
        await _provider(httpx.MockTransport(handler), retries=2).edit(_request(_png((800, 800))))
    assert calls["n"] == 2
    assert exc_info.value.retryable
    assert "не ответил вовремя" in exc_info.value.user_message


@pytest.mark.parametrize(
    ("status", "code", "error_type"),
    [
        (400, "moderation_blocked", ProviderRejectedError),
        (401, "invalid_api_key", ProviderConfigError),
        (429, "rate_limit_exceeded", ProviderUnavailableError),
    ],
)
async def test_openai_error_mapping(
    status: int, code: str, error_type: type[ProviderError]
) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(status, json={"error": {"code": code, "message": "nope"}})

    with pytest.raises(error_type):
        await _provider(httpx.MockTransport(handler), retries=2).edit(_request(_png((800, 800))))
    # Неповторяемые ошибки не ретраятся.
    assert calls["n"] == (2 if error_type.retryable else 1)


async def test_malformed_response_is_provider_error() -> None:
    transport = httpx.MockTransport(lambda r: httpx.Response(200, content=b"<html>"))
    with pytest.raises(ProviderError):
        await _provider(transport, retries=1).edit(_request(_png((800, 800))))


# ─────────────────────────── вспомогательное ───────────────────────────


def test_canvas_roundtrip_preserves_geometry() -> None:
    img = Image.new("RGB", (1000, 750), (0, 0, 0))
    img.paste((255, 255, 255), (450, 0, 550, 750))  # вертикальная полоса по центру
    canvas, layout = fit_to_canvas(img, [(1024, 1024), (1536, 1024), (1024, 1536)])
    assert canvas.size == (1536, 1024)
    restored = restore_from_canvas(canvas, layout)
    assert restored.size == (1000, 750)
    assert restored.getpixel((500, 375))[0] > 200
    assert restored.getpixel((300, 375))[0] < 30


def test_api_key_never_reaches_logs(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "json", [API_KEY])
    logging.getLogger("httpx").warning("POST with Authorization: Bearer %s", API_KEY)
    import structlog

    structlog.get_logger("t").info("calling", api_key=API_KEY, url=f"https://x/?k={API_KEY}")
    out = capsys.readouterr().out
    assert API_KEY not in out
    assert "***" in out
    lines = [json.loads(line) for line in out.strip().splitlines()]
    assert lines[-1]["api_key"] == "***"


def test_secret_masker_masks_bot_token() -> None:
    masker = SecretMasker()
    text = masker.mask_text(
        "https://api.telegram.org/bot123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw/getMe"
    )
    assert "AAHdqTcv" not in text


def test_large_upload_switches_to_jpeg_within_limit() -> None:
    import numpy as np

    from app.services.image_editing.openai_provider import UPLOAD_LIMIT_BYTES, upload_file

    # «Фотография» 4K: плавный градиент + зерно — PNG такого размера больше 10 МБ.
    rng = np.random.default_rng(0)
    yy, xx = np.mgrid[0:2560, 0:3840]
    base = np.dstack([xx / 15, yy / 10, (xx + yy) / 25]) % 255
    photo = np.clip(base + rng.normal(0, 12, base.shape), 0, 255).astype(np.uint8)
    name, data, mime = upload_file("source", Image.fromarray(photo))
    assert mime == "image/jpeg" and name == "source.jpg"
    assert len(data) <= UPLOAD_LIMIT_BYTES
    small_name, _, small_mime = upload_file("source", Image.new("RGB", (800, 600)))
    assert (small_name, small_mime) == ("source.png", "image/png")
