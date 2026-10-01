"""Проверка пригодности фото диска-референса (ракурс и качество)."""

from __future__ import annotations

import cv2
import numpy as np

from app.utils.images import open_image, pil_to_bgr


def assess_wheel_reference(data: bytes) -> list[str]:
    """Возвращает список предупреждений; пустой список — референс подходит."""
    warnings: list[str] = []
    image = pil_to_bgr(open_image(data))
    h, w = image.shape[:2]
    if min(h, w) < 500:
        warnings.append(f"низкое разрешение ({w}×{h}); лучше от 800 px по короткой стороне")

    scale = 640 / max(h, w)
    small = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if sharpness < 60:
        warnings.append("фото размыто — спицы могут получиться нечёткими")
    if float(gray.mean()) < 45:
        warnings.append("фото слишком тёмное")

    sh, sw = gray.shape
    min_r = int(min(sh, sw) * 0.2)
    circles = cv2.HoughCircles(
        cv2.medianBlur(gray, 5),
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min(sh, sw) // 2,
        param1=120,
        param2=45,
        minRadius=min_r,
        maxRadius=int(min(sh, sw) * 0.55),
    )
    if circles is None or not np.any(circles):
        warnings.append(
            "не удалось найти диск анфас — снимите диск прямо, чтобы он занимал большую часть кадра"
        )
    return warnings
