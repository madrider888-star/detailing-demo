"""Экспорт JPEG для объявлений: sRGB, ориентация, лимиты, EXIF, C2PA, отметка."""

from __future__ import annotations

import io
import re

import numpy as np
from PIL import Image, ImageCms

from app.core.config import Settings
from app.services.export.c2pa import embed_c2pa_png, extract_c2pa, make_test_jumbf
from app.services.export.normalizer import ExportOptions, normalize_for_export


def _image_bytes(
    size: tuple[int, int] = (1200, 800),
    fmt: str = "JPEG",
    mode: str = "RGB",
    **save: object,
) -> bytes:
    rng = np.random.default_rng(0)
    arr = rng.integers(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    arr[: size[1] // 2] = (200, 30, 30)  # верх — красный: проверка ориентации
    img = Image.fromarray(arr).convert(mode)
    buf = io.BytesIO()
    img.save(buf, fmt, **save)
    return buf.getvalue()


def _opts(**kw: object) -> ExportOptions:
    font = Settings(_env_file=None).font_path  # type: ignore[call-arg]
    return ExportOptions(font_path=font, **kw)  # type: ignore[arg-type]


def test_output_is_srgb_jpeg_with_quality_range() -> None:
    result = normalize_for_export(_image_bytes(fmt="PNG"), _opts())
    img = Image.open(io.BytesIO(result.data))
    assert img.format == "JPEG"
    assert img.mode == "RGB"
    profile = ImageCms.ImageCmsProfile(io.BytesIO(img.info["icc_profile"]))
    assert "srgb" in ImageCms.getProfileDescription(profile).lower()
    assert 90 <= result.quality <= 95


def test_orientation_is_applied_and_reset() -> None:
    exif = Image.Exif()
    exif[0x0112] = 6  # поворот на 90° по часовой
    raw = _image_bytes(size=(1200, 800), exif=exif.tobytes())
    result = normalize_for_export(raw, _opts())
    img = Image.open(io.BytesIO(result.data))
    assert img.size == (800, 1200)
    assert img.getexif()[0x0112] == 1
    # Красная половина после поворота на 90° по часовой оказывается справа.
    right = np.asarray(img)[:, -50:].reshape(-1, 3).mean(axis=0)
    assert right[0] > 150 and right[1] < 80


def test_max_side_is_respected() -> None:
    result = normalize_for_export(_image_bytes(size=(4000, 3000)), _opts(max_side=2000))
    assert max(result.width, result.height) == 2000
    assert Image.open(io.BytesIO(result.data)).size == (2000, 1500)


def test_size_limit_lowers_quality_then_resolution() -> None:
    raw = _image_bytes(size=(3000, 2000))  # шум плохо сжимается
    result = normalize_for_export(raw, _opts(max_side=3000, max_bytes=900_000))
    assert len(result.data) <= 900_000
    assert result.quality >= 90


def test_exif_is_clean_without_duplicates() -> None:
    exif = Image.Exif()
    exif[0x010F] = "Canon"
    exif[0x0110] = "EOS R6"
    exif[0x8298] = "Copyright someone"  # не из белого списка
    exif[0x9286] = "user comment junk"
    result = normalize_for_export(_image_bytes(exif=exif.tobytes()), _opts())
    out = Image.open(io.BytesIO(result.data)).getexif()
    assert out[0x010F] == "Canon"
    assert out[0x0110] == "EOS R6"
    assert 0x8298 not in out
    assert out.get_ifd(0x8769)[0xA001] == 1  # ColorSpace = sRGB
    # Ровно один APP1 (EXIF) сегмент.
    assert result.data.count(b"Exif\x00\x00") == 1


def test_transparent_and_cmyk_inputs() -> None:
    rgba = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
    buf = io.BytesIO()
    rgba.save(buf, "PNG")
    out = Image.open(io.BytesIO(normalize_for_export(buf.getvalue(), _opts()).data))
    assert out.getpixel((10, 10)) == (255, 255, 255)  # прозрачность → белый фон

    cmyk = _image_bytes(mode="CMYK")
    out = Image.open(io.BytesIO(normalize_for_export(cmyk, _opts()).data))
    assert out.mode == "RGB"


def test_visualization_label_is_added() -> None:
    plain = Image.new("RGB", (1600, 1000), (40, 40, 40))
    buf = io.BytesIO()
    plain.save(buf, "PNG")
    result = normalize_for_export(buf.getvalue(), _opts(label="Візуалізація"))
    img = np.asarray(Image.open(io.BytesIO(result.data))).astype(int)
    assert result.labeled
    corner = img[-60:, -260:]
    assert corner.max() > 150  # белый текст на плашке
    assert np.abs(img[:500, :500] - 40).max() < 6  # остальное не тронуто


def test_c2pa_manifest_is_preserved() -> None:
    jumbf = make_test_jumbf(b'{"claim":"x"}' * 10)
    png = embed_c2pa_png(_image_bytes(fmt="PNG"), jumbf)
    assert extract_c2pa(png) == jumbf
    result = normalize_for_export(png, _opts())
    assert result.c2pa_preserved
    assert extract_c2pa(result.data) == jumbf
    Image.open(io.BytesIO(result.data)).load()  # файл остаётся валидным JPEG


def test_large_c2pa_manifest_spans_segments() -> None:
    jumbf = make_test_jumbf(b"x" * 150_000)
    result = normalize_for_export(_image_bytes(), _opts(), provenance_fallback=jumbf)
    assert extract_c2pa(result.data) == jumbf
    segments = re.findall(rb"\xff\xeb..JP", result.data, flags=re.DOTALL)
    assert len(segments) >= 3  # 150 КБ не помещаются в один APP11 (≤ 64 КБ)
