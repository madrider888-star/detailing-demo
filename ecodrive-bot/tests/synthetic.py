"""Синтетические сцены для тестов: «автомобиль» с номером в перспективе."""

from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont

FONT = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "DejaVuSans-Bold.ttf"


def make_plate(text: str = "AA 1234 BB", size: tuple[int, int] = (520, 112)) -> NDArray[np.uint8]:
    w, h = size
    img = Image.new("RGB", (w, h), (244, 244, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, w - 1, h - 1), outline=(20, 20, 20), width=3)
    draw.rectangle((3, 3, 48, h - 4), fill=(0, 51, 153))
    draw.text(
        (26, h - 22),
        "UA",
        font=ImageFont.truetype(str(FONT), 18),
        fill=(255, 255, 255),
        anchor="mm",
    )
    draw.text(
        (w // 2 + 22, h // 2),
        text,
        font=ImageFont.truetype(str(FONT), 66),
        fill=(15, 15, 15),
        anchor="mm",
    )
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)  # type: ignore[no-any-return]


def make_scene(
    corners: NDArray[np.float32] | None = None,
    size: tuple[int, int] = (1280, 860),
    *,
    shade: float = 1.0,
    blur: float = 0.0,
    seed: int = 1,
) -> tuple[NDArray[np.uint8], NDArray[np.float32]]:
    w, h = size
    rng = np.random.default_rng(seed)
    yy = np.linspace(0, 1, h)[:, None]
    bg = np.dstack([90 + 40 * yy, 95 + 40 * yy, 100 + 40 * yy]).repeat(w, axis=1)
    scene = bg.astype(np.float32)
    # Кузов.
    cv2.rectangle(
        scene, (int(w * 0.15), int(h * 0.3)), (int(w * 0.85), int(h * 0.85)), (40, 40, 140), -1
    )
    cv2.rectangle(
        scene, (int(w * 0.2), int(h * 0.62)), (int(w * 0.8), int(h * 0.8)), (30, 30, 30), -1
    )
    # Фары.
    cv2.ellipse(scene, (int(w * 0.25), int(h * 0.45)), (60, 25), 0, 0, 360, (210, 210, 220), -1)
    cv2.ellipse(scene, (int(w * 0.75), int(h * 0.45)), (60, 25), 0, 0, 360, (210, 210, 220), -1)
    if corners is None:
        corners = np.array([[520, 600], [790, 590], [792, 650], [522, 664]], dtype=np.float32)
    plate = make_plate().astype(np.float32) * shade
    ph, pw = plate.shape[:2]
    src = np.array([[0, 0], [pw - 1, 0], [pw - 1, ph - 1], [0, ph - 1]], dtype=np.float32)
    m = cv2.getPerspectiveTransform(src, corners)
    warped = cv2.warpPerspective(plate, m, (w, h))
    mask = cv2.warpPerspective(np.ones((ph, pw), np.float32), m, (w, h))[..., None]
    scene = scene * (1 - mask) + warped * mask
    if blur:
        scene = cv2.GaussianBlur(scene, (0, 0), blur)
    scene += rng.normal(0, 2.0, scene.shape)
    return np.clip(scene, 0, 255).astype(np.uint8), corners


def to_jpeg_bytes(bgr: NDArray[np.uint8], quality: int = 92) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).save(buf, "JPEG", quality=quality)
    return buf.getvalue()
