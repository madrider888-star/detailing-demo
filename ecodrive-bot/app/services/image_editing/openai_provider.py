"""Реальный провайдер: OpenAI-совместимый endpoint `POST /images/edits`.

Работает с OpenAI (gpt-image-1) и с любым сервисом, повторяющим этот API
(Azure OpenAI, прокси-шлюзы). Ключ передаётся только в заголовке и не логируется.
"""

from __future__ import annotations

import base64
import binascii
from typing import Any, ClassVar

import httpx
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
    ProviderRejectedError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.utils.canvas import fit_mask_to_canvas, fit_to_canvas, restore_from_canvas
from app.utils.images import encode_png, open_image
from app.utils.retry import call_with_retry

log = get_logger(__name__)

SUPPORTED_SIZES: list[tuple[int, int]] = [(1024, 1024), (1536, 1024), (1024, 1536)]
_REJECT_CODES = {"moderation_blocked", "content_policy_violation", "image_generation_user_error"}


class OpenAIImageEditProvider(ImageEditingProvider):
    name: ClassVar[str] = "openai"
    supported_operations: ClassVar[frozenset[Operation]] = frozenset(
        {Operation.BACKGROUND, Operation.WHEELS, Operation.INTERIOR_COLOR, Operation.PLATE}
    )

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-image-1",
        quality: str = "high",
        input_fidelity: str | None = "high",
        timeout: float = 180.0,
        max_retries: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
        retry_initial_delay: float = 2.0,
    ) -> None:
        if not api_key:
            raise ProviderConfigError("OPENAI_API_KEY is not set")
        self.model = model
        self.quality = quality
        self.input_fidelity = input_fidelity
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

    async def _edit(self, request: EditRequest) -> EditResult:
        source = open_image(request.image)
        canvas, layout = fit_to_canvas(source, SUPPORTED_SIZES)
        files: list[tuple[str, tuple[str, bytes, str]]] = [
            ("image[]", ("source.png", encode_png(canvas), "image/png"))
        ]
        for idx, ref in enumerate(request.references):
            ref_png = encode_png(_flatten_reference(open_image(ref.data)))
            files.append(("image[]", (f"reference_{idx}_{ref.role}.png", ref_png, "image/png")))
        if request.mask is not None:
            mask_png = encode_png(fit_mask_to_canvas(open_image(request.mask), layout))
            files.append(("mask", ("mask.png", mask_png, "image/png")))

        data: dict[str, Any] = {
            "model": self.model,
            "prompt": request.prompt.render(),
            "size": layout.size_label,
            "quality": self.quality,
            "n": "1",
        }
        if self.input_fidelity:
            data["input_fidelity"] = self.input_fidelity

        async def _call() -> bytes:
            return await self._request(data, files)

        raw = await call_with_retry(
            _call, attempts=self.max_retries, initial_delay=self.retry_initial_delay
        )
        restored = encode_png(restore_from_canvas(open_image(raw), layout))
        # Провайдер может подписывать результат C2PA — не теряем манифест при обрезке полей.
        provenance = extract_c2pa(raw)
        if provenance is not None:
            restored = embed_c2pa_png(restored, provenance)
        return EditResult(
            image=restored,
            mime_type="image/png",
            provider=self.name,
            metadata={
                "model": self.model,
                "canvas": layout.size_label,
                "c2pa": provenance is not None,
            },
        )

    async def _request(
        self, data: dict[str, Any], files: list[tuple[str, tuple[str, bytes, str]]]
    ) -> bytes:
        try:
            response = await self._client.post("/images/edits", data=data, files=files)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("image edit request timed out") from exc
        except httpx.TransportError as exc:
            raise ProviderUnavailableError(f"transport error: {type(exc).__name__}") from exc

        if response.status_code >= 400:
            raise self._map_error(response)
        try:
            payload = response.json()
            b64 = payload["data"][0]["b64_json"]
            return base64.b64decode(b64, validate=True)
        except (ValueError, KeyError, IndexError, TypeError, binascii.Error) as exc:
            raise ProviderError("malformed provider response", retryable=True) from exc

    @staticmethod
    def _map_error(response: httpx.Response) -> ProviderError:
        status = response.status_code
        code = ""
        try:
            error = response.json().get("error") or {}
            code = str(error.get("code") or error.get("type") or "")
        except ValueError:
            pass
        log.warning("provider.http_error", provider="openai", status=status, code=code)
        if status in (401, 403):
            return ProviderConfigError(f"auth error {status}")
        if status == 429 or status >= 500:
            return ProviderUnavailableError(f"http {status} {code}")
        if code in _REJECT_CODES:
            return ProviderRejectedError(f"rejected: {code}")
        return ProviderError(f"http {status} {code}", retryable=False)


def _flatten_reference(image: Image.Image) -> Image.Image:
    """Прозрачность референса (скруглённые углы макета) — на светло-сером фоне."""
    if image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        base = Image.new("RGB", rgba.size, (210, 210, 210))
        base.paste(rgba, mask=rgba.getchannel("A"))
        return base
    return image.convert("RGB")
