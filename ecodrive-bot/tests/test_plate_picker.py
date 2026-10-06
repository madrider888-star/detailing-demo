"""Vision-модель выбирает номер машины среди кандидатов детектора."""

from __future__ import annotations

import json

import httpx
import numpy as np
import pytest

from app.core.config import Settings
from app.services.image_editing.base import ProviderError
from app.services.image_editing.openai_plate import OpenAIPlateProvider
from app.services.image_editing.plate_picker import (
    OpenAIPlatePicker,
    draw_candidates,
    parse_choice,
)
from app.services.plate_replacement.detector import PlateDetection
from tests.synthetic import make_scene, to_jpeg_bytes
from tests.test_openai_plate import _provider, _request, _solid


def _answer(text: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "output": [
                {"type": "reasoning", "summary": []},
                {"type": "message", "content": [{"type": "output_text", "text": text}]},
            ]
        },
    )


def _with_picker(
    settings: Settings, answer: httpx.Response, calls: list[str]
) -> OpenAIPlateProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/responses"):
            body = json.loads(request.content)
            assert body["input"][0]["content"][1]["image_url"].startswith("data:image/jpeg")
            return answer
        return _solid((1024, 1024), (90, 90, 90))

    provider = _provider(settings, handler)
    provider.picker = OpenAIPlatePicker(
        api_key="sk-test-0123456789abcdef",
        base_url="https://example.test/v1",
        transport=httpx.MockTransport(handler),
        max_retries=1,
        retry_initial_delay=0.01,
    )
    return provider


def test_parse_choice() -> None:
    assert parse_choice('{"plate": 2}', 3) == 1
    assert parse_choice('Answer: {"plate": 0}', 3) is None
    with pytest.raises(ProviderError):
        parse_choice('{"plate": 4}', 3)
    with pytest.raises(ProviderError):
        parse_choice("box two", 3)


def test_draw_candidates_is_jpeg() -> None:
    scene, truth = make_scene()
    det = PlateDetection(truth.astype(np.float32), 0.9, "contour", {})
    assert draw_candidates(scene, [det])[:2] == b"\xff\xd8"


async def test_vision_rejects_all_candidates_needs_review(settings: Settings) -> None:
    calls: list[str] = []
    provider = _with_picker(settings, _answer('{"plate": 0}'), calls)
    scene, _ = make_scene()
    source = to_jpeg_bytes(scene)
    result = await provider.edit(_request(source))
    assert result.needs_review
    assert result.image == source
    assert result.metadata["picked_by"] == "vision"
    assert not any(path.endswith("/images/edits") for path in calls)


async def test_vision_choice_overrides_detector_score(settings: Settings) -> None:
    calls: list[str] = []
    provider = _with_picker(settings, _answer('{"plate": 2}'), calls)
    scene, truth = make_scene()
    decoy = np.array([[10, 10], [130, 10], [130, 40], [10, 40]], np.float32)
    real = PlateDetection(truth.astype(np.float32), 0.61, "contour", {})

    class Stub:
        def detect(self, image: np.ndarray) -> list[PlateDetection]:
            return [PlateDetection(decoy, 0.95, "contour", {}), real]

    provider.replacer.detector = Stub()
    result = await provider.edit(_request(to_jpeg_bytes(scene)))
    assert not result.needs_review
    assert result.metadata["picked_by"] == "vision"
    assert result.metadata["confidence"] == 0.61


async def test_picker_failure_falls_back_to_detector_score(settings: Settings) -> None:
    calls: list[str] = []
    provider = _with_picker(settings, httpx.Response(500, json={}), calls)
    scene, _ = make_scene()
    result = await provider.edit(_request(to_jpeg_bytes(scene)))
    assert not result.needs_review
    assert result.metadata["picked_by"] == "score"
