"""Подгонка изображения под фиксированные размеры AI-провайдера без искажения пропорций.

Исходник дополняется полями (повтор крайних пикселей) до соотношения сторон, которое
принимает провайдер, а результат обрезается обратно и масштабируется до исходного
разрешения. Так геометрия автомобиля никогда не растягивается.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class CanvasLayout:
    orig_width: int
    orig_height: int
    canvas_width: int
    canvas_height: int
    pad_left: int
    pad_top: int
    content_width: int
    content_height: int

    @property
    def size_label(self) -> str:
        return f"{self.canvas_width}x{self.canvas_height}"


def choose_canvas(width: int, height: int, sizes: list[tuple[int, int]]) -> tuple[int, int]:
    aspect = width / height
    return min(sizes, key=lambda s: abs(np.log((s[0] / s[1]) / aspect)))


def fit_to_canvas(
    image: Image.Image, sizes: list[tuple[int, int]]
) -> tuple[Image.Image, CanvasLayout]:
    rgb = image.convert("RGB")
    cw, ch = choose_canvas(rgb.width, rgb.height, sizes)
    scale = min(cw / rgb.width, ch / rgb.height)
    content_w = max(1, round(rgb.width * scale))
    content_h = max(1, round(rgb.height * scale))
    resized = rgb.resize((content_w, content_h), Image.Resampling.LANCZOS)
    pad_left = (cw - content_w) // 2
    pad_top = (ch - content_h) // 2
    arr = np.asarray(resized)
    padded = np.pad(
        arr,
        (
            (pad_top, ch - content_h - pad_top),
            (pad_left, cw - content_w - pad_left),
            (0, 0),
        ),
        mode="edge",
    )
    layout = CanvasLayout(
        orig_width=rgb.width,
        orig_height=rgb.height,
        canvas_width=cw,
        canvas_height=ch,
        pad_left=pad_left,
        pad_top=pad_top,
        content_width=content_w,
        content_height=content_h,
    )
    return Image.fromarray(padded), layout


def restore_from_canvas(result: Image.Image, layout: CanvasLayout) -> Image.Image:
    """Обрезает поля и возвращает исходное разрешение."""
    rgb = result.convert("RGB")
    if rgb.size != (layout.canvas_width, layout.canvas_height):
        rgb = rgb.resize((layout.canvas_width, layout.canvas_height), Image.Resampling.LANCZOS)
    box = (
        layout.pad_left,
        layout.pad_top,
        layout.pad_left + layout.content_width,
        layout.pad_top + layout.content_height,
    )
    content = rgb.crop(box)
    return content.resize((layout.orig_width, layout.orig_height), Image.Resampling.LANCZOS)


def fit_mask_to_canvas(mask: Image.Image, layout: CanvasLayout) -> Image.Image:
    """Маска в той же раскладке, что и исходник; поля — непрозрачные (не редактировать)."""
    alpha = mask.convert("RGBA").getchannel("A")
    alpha = alpha.resize((layout.content_width, layout.content_height), Image.Resampling.NEAREST)
    canvas_alpha = Image.new("L", (layout.canvas_width, layout.canvas_height), 255)
    canvas_alpha.paste(alpha, (layout.pad_left, layout.pad_top))
    out = Image.new("RGBA", canvas_alpha.size, (0, 0, 0, 255))
    out.putalpha(canvas_alpha)
    return out
