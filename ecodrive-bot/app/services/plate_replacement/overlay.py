"""Фотореалистичное наложение фирменной таблички на найденный номер.

Все вычисления ведутся в «канонической» плоскости таблички (исходный номер,
выпрямленный по четырём углам), затем результат возвращается в перспективу кадра
одной гомографией и смешивается с фото через альфа-канал. Пиксели вне таблички не
меняются.

Учитывается:
* перспектива и наклон — гомография по четырём углам;
* яркость, тени и блики — карта освещённости исходного номера (символы удалены
  морфологическим закрытием) умножается на макет;
* цветовая температура — баланс каналов светлых участков исходного номера;
* размытие — подбор гауссова ядра под резкость исходного номера;
* шум/зерно — оценка шума исходника и добавление такого же;
* перекрытие рамкой или кузовом — тёмные массивные области у краёв номера
  остаются из оригинала.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.services.plate_replacement.geometry import expand_quad, quad_size
from app.utils.types import ImageArray, Quad

FloatImage = ImageArray
ImageBGR = ImageArray

TEMPLATE_WHITE = 250.0
_SIGMAS = (0.0, 0.35, 0.6, 0.85, 1.1, 1.4, 1.8, 2.3, 3.0, 4.0)


@dataclass(frozen=True)
class OverlayInfo:
    blur_sigma: float
    gain_mean: float
    color_cast: tuple[float, float, float]
    noise_sigma: float
    occluded_fraction: float


def _canon_corners(w: int, h: int) -> Quad:
    return np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)


def _laplacian_var(gray: ImageArray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_32F).var())


def estimate_illumination(gray: FloatImage) -> FloatImage:
    """Освещённость фона таблички: убираем тёмные символы и сглаживаем."""
    h = gray.shape[0]
    k = max(3, int(h * 0.45) | 1)
    closed = cv2.morphologyEx(
        gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    )
    sigma = max(1.0, h / 5)
    return cv2.GaussianBlur(closed, (0, 0), sigma)


def estimate_color_cast(plate: FloatImage, illum: FloatImage) -> ImageArray:
    gray = plate.mean(axis=2)
    mask = gray >= np.percentile(gray, 60)
    if mask.sum() < 10:
        return np.ones(3, dtype=np.float32)
    means = plate[mask].mean(axis=0)
    cast = means / max(float(means.mean()), 1e-3)
    # Исходный номер бывает цветным (жёлтый, зелёный), это не свет. Берём лишь
    # небольшую долю оттенка, чтобы не перекрашивать фирменную табличку.
    cast = 1.0 + 0.25 * (cast - 1.0)
    return np.clip(cast, 0.95, 1.05).astype(np.float32)


def estimate_noise(gray: FloatImage) -> float:
    residual = gray - cv2.medianBlur(gray.astype(np.uint8), 3).astype(np.float32)
    mad = float(np.median(np.abs(residual - np.median(residual))))
    return min(12.0, 1.4826 * mad)


def match_blur(template_gray: FloatImage, target_sharpness: float, max_sigma: float) -> float:
    best_sigma, best_err = 0.0, float("inf")
    for sigma in _SIGMAS:
        if sigma > max_sigma:
            break
        blurred = cv2.GaussianBlur(template_gray, (0, 0), sigma) if sigma else template_gray
        err = abs(np.log((_laplacian_var(blurred) + 1e-3) / (target_sharpness + 1e-3)))
        if err < best_err:
            best_sigma, best_err = sigma, err
    return best_sigma


def occlusion_mask(plate_gray: FloatImage, illum: FloatImage, plate_bgr: FloatImage) -> FloatImage:
    """Массивные тёмные области, касающиеся края номера (рамка, бампер, крюк)."""
    h, w = plate_gray.shape
    dark = (plate_gray < 0.55 * illum) | (plate_gray < 45)
    hsv = cv2.cvtColor(np.clip(plate_bgr, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
    blue_band = (hsv[..., 0] >= 95) & (hsv[..., 0] <= 130) & (hsv[..., 1] >= 80)
    dark &= ~blue_band
    k = max(3, round(h * 0.12))
    opened = cv2.morphologyEx(
        dark.astype(np.uint8) * 255,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)),
    )
    n, labels, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    mask: ImageArray = np.zeros((h, w), dtype=np.float32)
    for i in range(1, n):
        x, y, cw, ch, area = stats[i]
        if area < 0.01 * h * w:
            continue
        # Рамка/бампер заходят сверху или снизу широкой полосой; сбоку — только на всю
        # высоту. Символы номера под эти условия не попадают.
        touches_tb = (y <= 1 or y + ch >= h - 1) and cw >= 0.2 * w
        touches_lr = (x <= 1 or x + cw >= w - 1) and ch >= 0.9 * h
        if touches_tb or touches_lr:
            mask[labels == i] = 1.0
    if mask.any():
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        mask = cv2.GaussianBlur(mask, (0, 0), 1.0)
    return mask


def overlay_plate(
    image: ImageBGR,
    corners: Quad,
    template_rgba: ImageArray,
    *,
    expand: float = 0.03,
    seed: int = 0,
) -> tuple[ImageBGR, OverlayInfo]:
    """Накладывает RGBA-макет (в порядке каналов BGRA) на четырёхугольник `corners`."""
    quad = expand_quad(corners.astype(np.float32), expand, expand * 1.5)
    width, height = quad_size(quad)
    cw, ch = max(16, round(width)), max(6, round(height))
    canon = _canon_corners(cw, ch)

    # 1. Исходный номер в канонической плоскости.
    to_canon = cv2.getPerspectiveTransform(quad, canon)
    src_plate = cv2.warpPerspective(
        image, to_canon, (cw, ch), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    ).astype(np.float32)
    src_gray = cv2.cvtColor(src_plate, cv2.COLOR_BGR2GRAY)

    # 2. Макет в той же плоскости (premultiplied alpha → без тёмной каймы).
    tpl = cv2.resize(template_rgba, (cw, ch), interpolation=cv2.INTER_AREA).astype(np.float32)
    alpha: ImageArray = tpl[..., 3:4] / 255.0
    color: ImageArray = tpl[..., :3]

    # 3. Освещённость, тени, блики: макет «белый» = TEMPLATE_WHITE.
    illum = estimate_illumination(src_gray)
    gain = np.clip(illum / TEMPLATE_WHITE, 0.12, 1.15)[..., None]
    cast = estimate_color_cast(src_plate, illum)
    color = color * gain * cast[None, None, :]

    # 4. Размытие под резкость исходника.
    sharp_src = _laplacian_var(src_gray)
    sigma = match_blur(cv2.cvtColor(np.clip(color, 0, 255), cv2.COLOR_BGR2GRAY), sharp_src, ch / 8)
    if sigma:
        color = cv2.GaussianBlur(color * alpha, (0, 0), sigma)
        alpha_b = cv2.GaussianBlur(alpha[..., 0], (0, 0), sigma)[..., None]
        color = np.where(alpha_b > 1e-3, color / np.maximum(alpha_b, 1e-3), color)
        alpha = alpha_b

    # 5. Зерно.
    noise = estimate_noise(src_gray)
    if noise > 0.5:
        rng = np.random.default_rng(seed)
        color = color + rng.normal(0, noise, size=color.shape[:2])[..., None].astype(np.float32)

    # 6. Перекрытия рамкой/кузовом — оставляем пиксели оригинала.
    occ = occlusion_mask(src_gray, illum, src_plate)
    alpha = alpha * (1.0 - occ[..., None])

    # 7. Обратно в перспективу кадра.
    to_image = cv2.getPerspectiveTransform(canon, quad)
    h, w = image.shape[:2]
    premult = np.concatenate([np.clip(color, 0, 255) * alpha, alpha * 255.0], axis=2)
    warped = cv2.warpPerspective(
        premult,
        to_image,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )
    a = np.clip(warped[..., 3:4] / 255.0, 0.0, 1.0)
    out = warped[..., :3] + image.astype(np.float32) * (1.0 - a)
    result = np.clip(out + 0.5, 0, 255).astype(np.uint8)

    info = OverlayInfo(
        blur_sigma=float(sigma),
        gain_mean=float(gain.mean()),
        color_cast=(float(cast[0]), float(cast[1]), float(cast[2])),
        noise_sigma=float(noise),
        occluded_fraction=float(occ.mean()),
    )
    return result, info
