"""Небольшие помощники для конвертации изображений."""

from __future__ import annotations

import io

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.utils.types import ImageArray


def open_image(data: bytes) -> Image.Image:
    """Открывает изображение и сразу применяет EXIF-ориентацию."""
    image = Image.open(io.BytesIO(data))
    image.load()
    return ImageOps.exif_transpose(image)


def pil_to_bgr(image: Image.Image) -> ImageArray:
    rgb = np.asarray(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def bgr_to_pil(array: ImageArray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(array, cv2.COLOR_BGR2RGB))


def encode_png(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=False)
    return buf.getvalue()
