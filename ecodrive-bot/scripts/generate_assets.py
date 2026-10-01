"""Генерирует макет фирменной таблички и фоны-заглушки.

Запуск:  python scripts/generate_assets.py [--force]

Файлы — стартовые заготовки. Замените их реальным макетом от дизайнера и
настоящими фотографиями студий (см. README, разделы о табличке и фонах).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_BOLD = ROOT / "assets" / "fonts" / "DejaVuSans-Bold.ttf"
GREEN = (30, 158, 90)
DARK = (22, 28, 34)


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD), size)


def branded_plate(path: Path) -> None:
    """Табличка 1040×224 (пропорции EU 520×112 мм), прозрачные скруглённые углы."""
    w, h = 1040, 224
    plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(plate)
    draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=22, fill=(250, 250, 250, 255))
    draw.rounded_rectangle((7, 7, w - 8, h - 8), radius=17, outline=(*DARK, 255), width=6)
    # Зелёная полоса бренда слева.
    band_w = 118
    draw.rounded_rectangle((13, 13, 13 + band_w, h - 14), radius=12, fill=(*GREEN, 255))
    # Лист: две дуги, сходящиеся остриями, повёрнутые на 35°.
    t = np.linspace(0, np.pi, 40)
    lx = np.concatenate([np.sin(t) * 26, -np.sin(t[::-1]) * 26])
    ly = np.concatenate([-np.cos(t) * 50, -np.cos(t[::-1]) * 50])
    a = np.deg2rad(35)
    leaf = [
        (72 + x * np.cos(a) - y * np.sin(a), 100 + x * np.sin(a) + y * np.cos(a))
        for x, y in zip(lx, ly, strict=False)
    ]
    draw.polygon(leaf, fill=(255, 255, 255, 255))
    vx, vy = 44 * np.sin(a), 44 * np.cos(a)
    draw.line((72 + vx, 100 - vy, 72 - vx * 0.9, 100 + vy * 0.9), fill=(*GREEN, 255), width=5)
    draw.text((72, 182), "ECO", font=_font(30), fill=(255, 255, 255, 255), anchor="mm")
    # Название.
    draw.text((598, 100), "ECODRIVE", font=_font(118), fill=(*DARK, 255), anchor="mm")
    draw.text((598, 186), "A U T O", font=_font(40), fill=(*GREEN, 255), anchor="mm")
    path.parent.mkdir(parents=True, exist_ok=True)
    plate.save(path, optimize=True)


def _vertical_gradient(w: int, h: int, top: tuple[int, ...], bottom: tuple[int, ...]) -> np.ndarray:
    t = np.linspace(0, 1, h)[:, None, None]
    grad = np.array(top)[None, None, :] * (1 - t) + np.array(bottom)[None, None, :] * t
    return np.repeat(grad, w, axis=1)


def _studio(
    w: int, h: int, wall: tuple[int, int, int], floor: tuple[int, int, int], glow: float
) -> Image.Image:
    horizon = int(h * 0.62)
    arr = np.zeros((h, w, 3))
    arr[:horizon] = _vertical_gradient(w, horizon, tuple(min(255, c + 18) for c in wall), wall)
    arr[horizon:] = _vertical_gradient(w, h - horizon, floor, tuple(max(0, c - 25) for c in floor))
    yy, xx = np.mgrid[0:h, 0:w]
    spot = np.exp(-(((xx - w / 2) / (w * 0.45)) ** 2 + ((yy - h * 0.45) / (h * 0.5)) ** 2))
    arr += glow * spot[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return img.filter(ImageFilter.GaussianBlur(2))


def _showroom(w: int, h: int) -> Image.Image:
    img = _studio(w, h, (214, 218, 222), (196, 198, 200), 25)
    draw = ImageDraw.Draw(img)
    horizon = int(h * 0.62)
    for i in range(7):
        x0 = int(w * (0.04 + i * 0.135))
        draw.rectangle((x0, int(h * 0.12), x0 + int(w * 0.11), horizon - 20), fill=(178, 204, 222))
    draw.rectangle((0, int(h * 0.08), w, int(h * 0.11)), fill=(240, 240, 240))
    return img.filter(ImageFilter.GaussianBlur(3))


def _city(w: int, h: int) -> Image.Image:
    arr = _vertical_gradient(w, h, (120, 160, 205), (225, 214, 196))
    img = Image.fromarray(arr.astype(np.uint8))
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(7)
    horizon = int(h * 0.66)
    x = 0
    while x < w:
        bw = int(rng.integers(w // 18, w // 8))
        bh = int(rng.integers(h // 5, h // 2))
        shade = int(rng.integers(70, 120))
        draw.rectangle((x, horizon - bh, x + bw, horizon), fill=(shade, shade + 6, shade + 14))
        x += bw + int(rng.integers(2, 12))
    draw.rectangle((0, horizon, w, h), fill=(84, 86, 90))
    draw.rectangle((0, horizon, w, horizon + 8), fill=(150, 150, 150))
    return img.filter(ImageFilter.GaussianBlur(4))


def _road(w: int, h: int) -> Image.Image:
    arr = _vertical_gradient(w, h, (110, 165, 225), (215, 230, 240))
    img = Image.fromarray(arr.astype(np.uint8))
    draw = ImageDraw.Draw(img)
    horizon = int(h * 0.58)
    draw.rectangle((0, horizon, w, h), fill=(118, 142, 92))
    draw.polygon(
        [(w * 0.46, horizon), (w * 0.54, horizon), (w * 1.1, h), (-w * 0.1, h)], fill=(70, 72, 76)
    )
    for i in range(6):
        y0 = horizon + (h - horizon) * (i / 6) ** 1.6
        y1 = horizon + (h - horizon) * ((i + 0.5) / 6) ** 1.6
        draw.polygon(
            [
                (w / 2 - 2 - i * 3, y0),
                (w / 2 + 2 + i * 3, y0),
                (w / 2 + 3 + i * 4, y1),
                (w / 2 - 3 - i * 4, y1),
            ],
            fill=(230, 230, 220),
        )
    return img.filter(ImageFilter.GaussianBlur(2))


def backgrounds(folder: Path, force: bool) -> None:
    w, h = 1920, 1280
    makers = {
        "white_studio.jpg": lambda: _studio(w, h, (236, 236, 238), (222, 222, 224), 18),
        "dark_studio.jpg": lambda: _studio(w, h, (28, 30, 34), (40, 42, 46), 45),
        "showroom.jpg": lambda: _showroom(w, h),
        "city.jpg": lambda: _city(w, h),
        "road.jpg": lambda: _road(w, h),
        "neutral_gray.jpg": lambda: _studio(w, h, (128, 128, 130), (118, 118, 120), 12),
    }
    folder.mkdir(parents=True, exist_ok=True)
    for name, make in makers.items():
        target = folder / name
        if target.exists() and not force:
            continue
        make().save(target, quality=88, optimize=True, progressive=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="перезаписать существующие файлы")
    args = parser.parse_args()
    plate_path = ROOT / "assets" / "branded_plate" / "ecodrive_plate.png"
    if args.force or not plate_path.exists():
        branded_plate(plate_path)
    backgrounds(ROOT / "assets" / "backgrounds", args.force)
    print("assets ready")


if __name__ == "__main__":
    main()
