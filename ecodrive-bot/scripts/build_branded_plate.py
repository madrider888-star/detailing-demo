"""Собирает макет таблички из исходника логотипа владельца.

Пропорции и отступы сняты с фото на ecodrive.in.ua (табличка на BYD): табличка
≈ 2.9:1, блок «логотип + ECODRIVE AUTO» занимает ≈ 77 % ширины и ≈ 64 % высоты,
небольшие скругления углов.

Запуск: python scripts/build_branded_plate.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "branded_plate" / "ecodrive_logo_source.png"
TARGET = ROOT / "assets" / "branded_plate" / "ecodrive_plate.png"

ASPECT = 2.9
BLOCK_W, BLOCK_H = 0.77, 0.64
CORNER = 0.09  # радиус скругления относительно высоты
SCALE = 2  # макет в 2 раза крупнее исходника — запас резкости


def main() -> None:
    src = Image.open(SOURCE).convert("RGBA")
    arr = np.asarray(src).astype(int)
    content = (arr[..., :3].max(axis=2) > 60) & (arr[..., 3] > 200)
    ys, xs = np.where(content)
    pad = 4
    block = src.crop((xs.min() - pad, ys.min() - pad, xs.max() + pad + 1, ys.max() + pad + 1))
    block = block.resize((block.width * SCALE, block.height * SCALE), Image.Resampling.LANCZOS)

    height = round(max(block.height / BLOCK_H, block.width / BLOCK_W / ASPECT))
    width = round(height * ASPECT)
    plate = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    radius = round(height * CORNER)
    ImageDraw.Draw(plate).rounded_rectangle(
        (0, 0, width - 1, height - 1), radius=radius, fill=(0, 0, 0, 255)
    )
    # Блок с чёрным фоном исходника — вклеиваем по центру (непрозрачные пиксели).
    bx, by = (width - block.width) // 2, (height - block.height) // 2
    plate.alpha_composite(block, (bx, by))
    plate.save(TARGET, optimize=True)
    print(f"{TARGET.name}: {width}x{height} (aspect {width / height:.2f})")


if __name__ == "__main__":
    main()
