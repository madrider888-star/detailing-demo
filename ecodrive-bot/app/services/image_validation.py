"""Проверка загружаемых изображений: реальный формат, размер, защита от «бомб»."""

from __future__ import annotations

import io
import warnings
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

from app.core.errors import ImageValidationError

ALLOWED_FORMATS: dict[str, str] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}
ALLOWED_DECLARED_MIME = frozenset({*ALLOWED_FORMATS.values(), "image/jpg", "image/pjpeg"})

# Сигнатуры, которые никогда не являются фотографией.
_FORBIDDEN_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"MZ", "исполняемый файл Windows"),
    (b"\x7fELF", "исполняемый файл Linux"),
    (b"\xca\xfe\xba\xbe", "исполняемый файл macOS"),
    (b"\xcf\xfa\xed\xfe", "исполняемый файл macOS"),
    (b"#!", "скрипт"),
    (b"PK\x03\x04", "архив"),
    (b"%PDF", "PDF-документ"),
    (b"Rar!", "архив"),
    (b"7z\xbc\xaf", "архив"),
    (b"<", "HTML/SVG/XML"),
)
_EXT_FOR_MIME = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


@dataclass(frozen=True)
class ValidatedImage:
    data: bytes
    mime_type: str
    format: str
    width: int
    height: int

    @property
    def extension(self) -> str:
        return _EXT_FOR_MIME[self.mime_type]


def sniff_mime(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(
    data: bytes,
    *,
    declared_mime: str | None = None,
    max_bytes: int,
    max_pixels: int,
    min_side: int,
) -> ValidatedImage:
    if not data:
        raise ImageValidationError("empty", user_message="Файл пустой.")
    if len(data) > max_bytes:
        raise ImageValidationError(
            "too large",
            user_message=f"Файл слишком большой (максимум {max_bytes // (1024 * 1024)} МБ).",
        )
    stripped = data.lstrip()
    for signature, label in _FORBIDDEN_SIGNATURES:
        if stripped.startswith(signature):
            raise ImageValidationError(
                f"forbidden signature: {label}",
                user_message=f"Это не изображение ({label}). Отправьте фото в JPEG, PNG или WEBP.",
            )
    if declared_mime and declared_mime.lower() not in ALLOWED_DECLARED_MIME:
        raise ImageValidationError(
            f"declared mime {declared_mime}",
            user_message="Поддерживаются только изображения JPEG, PNG и WEBP.",
        )
    sniffed = sniff_mime(data)
    if sniffed is None:
        raise ImageValidationError(
            "unknown signature",
            user_message="Не удалось распознать изображение. Отправьте JPEG, PNG или WEBP.",
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as probe:
                fmt = probe.format or ""
                width, height = probe.size
                if width * height > max_pixels:
                    raise ImageValidationError(
                        "too many pixels",
                        user_message="Слишком большое разрешение изображения.",
                    )
                probe.verify()
            # verify() не декодирует пиксели — проверяем, что файл реально читается.
            with Image.open(io.BytesIO(data)) as full:
                full.load()
    except ImageValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Warning) as exc:
        raise ImageValidationError(
            f"decode failed: {exc}",
            user_message="Файл повреждён или не является изображением.",
        ) from exc

    real_mime = ALLOWED_FORMATS.get(fmt)
    if real_mime is None or real_mime != sniffed:
        raise ImageValidationError(
            f"format mismatch {fmt}/{sniffed}",
            user_message="Поддерживаются только изображения JPEG, PNG и WEBP.",
        )
    if min(width, height) < min_side:
        raise ImageValidationError(
            "too small",
            user_message=(
                f"Слишком маленькое изображение ({width}×{height}). "
                f"Нужно не меньше {min_side} px по короткой стороне."
            ),
        )
    return ValidatedImage(data=data, mime_type=real_mime, format=fmt, width=width, height=height)
