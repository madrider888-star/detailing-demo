"""Нормализация экспортируемых файлов для публикации в объявлениях (AutoRIA и др.).

* JPEG, качество 90–95 %;
* цветовой профиль sRGB (конвертация из встроенного ICC + встраивание sRGB);
* корректная ориентация (EXIF Orientation применяется к пикселям, тег = 1);
* ограничение максимального разрешения и размера файла;
* чистый EXIF без повреждённых и дублирующихся полей (собирается заново);
* C2PA Content Credentials сохраняются, видимые отметки не удаляются;
* для существенно изменённых фото — небольшая отметка «Візуалізація».

Модуль не содержит и не должен содержать функций для обхода модерации или
скрытия факта редактирования.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps

from app.core.logging import get_logger
from app.services.export.c2pa import embed_c2pa_jpeg, extract_c2pa

log = get_logger(__name__)

SOFTWARE_TAG = "EcoDrive Auto Bot"
_EXIF_IFD = 0x8769
_TAG_ORIENTATION = 0x0112
_TAG_MAKE, _TAG_MODEL = 0x010F, 0x0110
_TAG_SOFTWARE, _TAG_DATETIME = 0x0131, 0x0132
_TAG_DATETIME_ORIGINAL, _TAG_COLOR_SPACE = 0x9003, 0xA001


@dataclass(frozen=True)
class ExportOptions:
    max_side: int = 2560
    quality: int = 92
    min_quality: int = 90
    max_bytes: int = 8 * 1024 * 1024
    label: str | None = None
    font_path: Path | None = None


@dataclass(frozen=True)
class ExportResult:
    data: bytes
    width: int
    height: int
    quality: int
    labeled: bool
    c2pa_preserved: bool
    mime_type: str = "image/jpeg"


@lru_cache(maxsize=1)
def srgb_profile_bytes() -> bytes:
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def _to_srgb(image: Image.Image) -> Image.Image:
    icc = image.info.get("icc_profile")
    if image.mode == "CMYK" and not icc:
        return image.convert("RGB")
    if not icc:
        return image
    try:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        description = (ImageCms.getProfileDescription(src) or "").lower()
        if "srgb" in description and image.mode in ("RGB", "RGBA", "L", "LA"):
            return image
        if image.mode not in ("RGB", "CMYK", "L"):
            image = image.convert("RGB")
        out_mode = "RGB"
        converted = ImageCms.profileToProfile(
            image,
            src,
            ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")),
            renderingIntent=ImageCms.Intent.PERCEPTUAL,
            outputMode=out_mode,
        )
        return converted if converted is not None else image
    except (OSError, ImageCms.PyCMSError) as exc:  # повреждённый профиль
        log.warning("export.icc_failed", error=str(exc))
        return image


def _flatten(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA", "PA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, (255, 255, 255))
        canvas.paste(rgba, mask=rgba.getchannel("A"))
        return canvas
    return image.convert("RGB")


def _clean_exif(source: Image.Image) -> bytes:
    """Новый EXIF: только безопасные поля, без дублей, Orientation = 1."""
    clean = Image.Exif()
    try:
        original = source.getexif()
        for tag in (_TAG_MAKE, _TAG_MODEL):
            value = original.get(tag)
            if isinstance(value, str) and value.isprintable() and len(value) < 64:
                clean[tag] = value.strip("\x00 ")
        exif_ifd = original.get_ifd(_EXIF_IFD)
        dto = exif_ifd.get(_TAG_DATETIME_ORIGINAL)
    except Exception:
        dto = None
    clean[_TAG_ORIENTATION] = 1
    clean[_TAG_SOFTWARE] = SOFTWARE_TAG
    clean[_TAG_DATETIME] = datetime.now(UTC).strftime("%Y:%m:%d %H:%M:%S")
    sub = clean.get_ifd(_EXIF_IFD)
    sub[_TAG_COLOR_SPACE] = 1  # sRGB
    if isinstance(dto, str) and len(dto) == 19:
        sub[_TAG_DATETIME_ORIGINAL] = dto
    return clean.tobytes()


def _load_font(font_path: Path | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path and font_path.is_file():
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default(size=size)


def add_visualization_label(
    image: Image.Image, text: str, font_path: Path | None = None
) -> Image.Image:
    """Небольшая полупрозрачная плашка в правом нижнем углу."""
    base = image.convert("RGBA")
    short = min(base.size)
    font = _load_font(font_path, max(12, round(short * 0.022)))
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    tw, th = right - left, bottom - top
    pad = max(4, round(th * 0.45))
    margin = max(8, round(short * 0.018))
    x1, y1 = base.width - margin, base.height - margin
    x0, y0 = x1 - tw - pad * 2, y1 - th - pad * 2
    draw.rounded_rectangle((x0, y0, x1, y1), radius=pad, fill=(0, 0, 0, 120))
    draw.text((x0 + pad - left, y0 + pad - top), text, font=font, fill=(255, 255, 255, 230))
    return Image.alpha_composite(base, layer).convert("RGB")


def _encode(image: Image.Image, quality: int, exif: bytes) -> bytes:
    buf = io.BytesIO()
    image.save(
        buf,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
        subsampling="4:2:0" if quality < 93 else "4:4:4",
        icc_profile=srgb_profile_bytes(),
        exif=exif,
    )
    return buf.getvalue()


def normalize_for_export(
    data: bytes, options: ExportOptions, *, provenance_fallback: bytes | None = None
) -> ExportResult:
    """`provenance_fallback` — JUMBF исходного файла: если результат провайдера
    манифеста не содержит, сохраняем манифест оригинала."""
    c2pa = extract_c2pa(data) or provenance_fallback
    with Image.open(io.BytesIO(data)) as opened:
        opened.load()
        exif = _clean_exif(opened)
        image = ImageOps.exif_transpose(opened)
        image = _flatten(_to_srgb(image))

    if max(image.size) > options.max_side:
        image.thumbnail((options.max_side, options.max_side), Image.Resampling.LANCZOS)

    labeled = bool(options.label)
    if options.label:
        image = add_visualization_label(image, options.label, options.font_path)

    quality = options.quality
    encoded = _encode(image, quality, exif)
    while len(encoded) > options.max_bytes:
        if quality > options.min_quality:
            quality -= 1
        else:
            # Качество не опускаем ниже минимума — уменьшаем разрешение.
            new_size = (round(image.width * 0.88), round(image.height * 0.88))
            if min(new_size) < 320:
                break
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        encoded = _encode(image, quality, exif)

    if c2pa is not None:
        encoded = embed_c2pa_jpeg(encoded, c2pa)
    return ExportResult(
        data=encoded,
        width=image.width,
        height=image.height,
        quality=quality,
        labeled=labeled,
        c2pa_preserved=c2pa is not None,
    )
