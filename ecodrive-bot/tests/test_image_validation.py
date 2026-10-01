"""Валидация входящих изображений: MIME, реальный формат, размеры, исполняемые файлы."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.core.errors import ImageValidationError
from app.services.image_validation import validate_image

LIMITS = {"max_bytes": 5 * 1024 * 1024, "max_pixels": 30_000_000, "min_side": 320}


def _img(fmt: str, size: tuple[int, int] = (800, 600)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (10, 120, 60)).save(buf, fmt)
    return buf.getvalue()


@pytest.mark.parametrize(
    ("fmt", "mime"), [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")]
)
def test_accepts_supported_formats(fmt: str, mime: str) -> None:
    result = validate_image(_img(fmt), declared_mime=mime, **LIMITS)
    assert result.mime_type == mime
    assert (result.width, result.height) == (800, 600)


@pytest.mark.parametrize(
    "payload",
    [
        b"MZ\x90\x00\x03" + b"\x00" * 200,
        b"\x7fELF\x02\x01\x01" + b"\x00" * 200,
        b"#!/bin/sh\nrm -rf /\n",
        b"PK\x03\x04" + b"\x00" * 200,
        b"%PDF-1.7\n",
        b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>",
    ],
)
def test_rejects_executables_and_non_images(payload: bytes) -> None:
    with pytest.raises(ImageValidationError):
        validate_image(payload, declared_mime="image/jpeg", **LIMITS)


def test_rejects_disallowed_declared_mime() -> None:
    with pytest.raises(ImageValidationError):
        validate_image(_img("JPEG"), declared_mime="application/x-msdownload", **LIMITS)


def test_real_format_wins_over_extension() -> None:
    # Объявлено как JPEG, а на деле GIF → не принимаем.
    with pytest.raises(ImageValidationError):
        validate_image(_img("GIF"), declared_mime="image/jpeg", **LIMITS)


def test_rejects_truncated_file() -> None:
    data = _img("JPEG")
    with pytest.raises(ImageValidationError):
        validate_image(data[: len(data) // 3], declared_mime="image/jpeg", **LIMITS)


def test_rejects_too_small_and_too_large() -> None:
    with pytest.raises(ImageValidationError, match="small"):
        validate_image(_img("PNG", (200, 150)), **LIMITS)
    with pytest.raises(ImageValidationError, match="large"):
        validate_image(_img("PNG"), max_bytes=100, max_pixels=10**8, min_side=10)
    with pytest.raises(ImageValidationError, match="pixels"):
        validate_image(
            _img("PNG", (3000, 3000)), max_bytes=10**8, max_pixels=1_000_000, min_side=10
        )


def test_rejects_empty() -> None:
    with pytest.raises(ImageValidationError):
        validate_image(b"", **LIMITS)
