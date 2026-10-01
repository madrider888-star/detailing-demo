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
        _, y, cw, ch, area = stats[i]
        if area < 0.01 * h * w:
            continue
        # Рамка/бампер заходят сверху или снизу широкой полосой. Тёмные края слева и
        # справа (EU-полоса, кант номера, кузов) перекрытием не считаем — иначе из-под
        # макета выглядывает старый номер. Символы под условие тоже не попадают.
        if (y <= 1 or y + ch >= h - 1) and cw >= 0.2 * w:
            mask[labels == i] = 1.0
    if mask.any():
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        mask = cv2.GaussianBlur(mask, (0, 0), 1.0)
    return mask


ASPECT_TOLERANCE = 1.1  # отличие пропорций, при котором макет ещё растягивается по номеру


EU_PLATE_ASPECT = 520 / 112  # реальные пропорции номера; в кадре они искажены перспективой


DEFAULT_HEIGHT_RATIO = 1.5  # высота макета другой формы относительно высоты номера


def template_box(
    plate_w: int,
    plate_h: int,
    template_aspect: float,
    plate_aspect: float = EU_PLATE_ASPECT,
    height_ratio: float = DEFAULT_HEIGHT_RATIO,
) -> tuple[float, float, float, float]:
    """Прямоугольник макета в плоскости номера (x0, y0, x1, y1), в пикселях `plate_w×plate_h`.

    Расчёт ведётся в реальных пропорциях номера (520×112 мм), а не в видимых: на
    снимке под углом номер кажется короче, но гомография вернёт перспективу.
    Если пропорции макета близки к номеру — макет занимает номер целиком. Иначе
    макет сохраняет свои пропорции, его высота = `height_ratio` × высота номера,
    центр — в центре номера. Видимые остатки старого номера закрашиваются отдельно.
    """
    if abs(np.log(template_aspect / plate_aspect)) < np.log(ASPECT_TOLERANCE):
        return 0.0, 0.0, float(plate_w), float(plate_h)
    # Единицы: ширина номера = 1, высота = 1 / plate_aspect.
    th = height_ratio / plate_aspect
    tw = th * template_aspect
    sx, sy = float(plate_w), float(plate_h) * plate_aspect
    x0, y0 = (1 - tw) / 2 * sx, (1 / plate_aspect - th) / 2 * sy
    return x0, y0, x0 + tw * sx, y0 + th * sy


def fitted_quad(
    corners: Quad,
    template_aspect: float,
    expand: float = 0.03,
    height_ratio: float = DEFAULT_HEIGHT_RATIO,
) -> Quad:
    """Четырёхугольник в кадре, куда ляжет макет (с учётом перспективы номера)."""
    quad = expand_quad(corners.astype(np.float32), expand, expand * 1.5)
    width, height = quad_size(quad)
    cw, ch = max(16, round(width)), max(6, round(height))
    x0, y0, x1, y1 = template_box(cw, ch, template_aspect, height_ratio=height_ratio)
    to_image = cv2.getPerspectiveTransform(_canon_corners(cw, ch), quad)
    box = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.float32)
    return cv2.perspectiveTransform(box.reshape(1, 4, 2), to_image).reshape(4, 2)


def _shift(src: ImageArray, x0: float, y0: float, size: tuple[int, int], border: int) -> ImageArray:
    """Переносит карту из плоскости номера в плоскость макета (сдвиг на x0, y0)."""
    matrix = np.array([[1, 0, -x0], [0, 1, -y0]], dtype=np.float32)
    return cv2.warpAffine(src, matrix, size, flags=cv2.INTER_LINEAR, borderMode=border)


def remove_old_plate(image: ImageBGR, corners: Quad, noise_sigma: float, seed: int) -> ImageBGR:
    """Закрашивает старый номер окружающим фоном (там, где его не закроет макет)."""
    region = expand_quad(corners.astype(np.float32), 0.06, 0.16)
    h, w = image.shape[:2]
    x0, y0 = np.floor(region.min(axis=0)).astype(int) - 8
    x1, y1 = np.ceil(region.max(axis=0)).astype(int) + 8
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return image
    roi = image[y0:y1, x0:x1]
    mask = np.zeros(roi.shape[:2], np.uint8)
    cv2.fillConvexPoly(mask, np.round(region - [x0, y0]).astype(np.int32), 255)
    _, plate_h = quad_size(corners)
    filled = cv2.inpaint(roi, mask, max(3.0, plate_h * 0.2), cv2.INPAINT_TELEA)
    if noise_sigma > 0.5:  # у закрашенной области должно быть то же зерно, что у фото
        rng = np.random.default_rng(seed + 1)
        grain = rng.normal(0, noise_sigma, size=filled.shape[:2])[..., None]
        noisy = np.clip(filled.astype(np.float32) + grain, 0, 255).astype(np.uint8)
        filled = np.where(mask[..., None] > 0, noisy, filled)
    out = image.copy()
    out[y0:y1, x0:x1] = filled
    return out


def add_rim_and_sheen(color: ImageArray, alpha: ImageArray) -> ImageArray:
    """Светлый кант по краю и лёгкий блик сверху — табличка выглядит объёмной, а не наклейкой."""
    a = alpha[..., 0]
    h = a.shape[0]
    k = max(2, round(h * 0.03))
    inner = cv2.erode(a, np.ones((k, k), np.uint8))
    rim = np.clip(a - inner, 0, 1)
    rim = cv2.GaussianBlur(rim, (0, 0), max(0.6, k / 3))[..., None]
    color = color * (1 - 0.55 * rim) + 150.0 * 0.55 * rim
    sheen = np.linspace(1.0, 0.0, h, dtype=np.float32)[:, None, None] ** 2
    return color + 16.0 * sheen  # type: ignore[no-any-return]


def overlay_plate(
    image: ImageBGR,
    corners: Quad,
    template_rgba: ImageArray,
    *,
    expand: float = 0.03,
    height_ratio: float = DEFAULT_HEIGHT_RATIO,
    seed: int = 0,
) -> tuple[ImageBGR, OverlayInfo]:
    """Накладывает RGBA-макет (в порядке каналов BGRA) на номер `corners`."""
    quad = expand_quad(corners.astype(np.float32), expand, expand * 1.5)
    width, height = quad_size(quad)
    cw, ch = max(16, round(width)), max(6, round(height))
    canon = _canon_corners(cw, ch)

    # 1. Исходный номер в канонической плоскости: отсюда берём свет, резкость, шум.
    to_canon = cv2.getPerspectiveTransform(quad, canon)
    src_plate = cv2.warpPerspective(
        image, to_canon, (cw, ch), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    ).astype(np.float32)
    src_gray = cv2.cvtColor(src_plate, cv2.COLOR_BGR2GRAY)
    illum = estimate_illumination(src_gray)
    occ_plate = occlusion_mask(src_gray, illum, src_plate)

    # Где лежит макет: его пропорции сохраняются.
    th_, tw_ = template_rgba.shape[:2]
    x0, y0, x1, y1 = template_box(cw, ch, tw_ / th_, height_ratio=height_ratio)
    covers_plate = x0 <= 0 and y0 <= 0 and x1 >= cw and y1 >= ch
    tcw, tch = max(16, round(x1 - x0)), max(6, round(y1 - y0))
    target_box = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.float32)
    plate_to_image = cv2.getPerspectiveTransform(canon, quad)
    target_quad = cv2.perspectiveTransform(target_box.reshape(1, 4, 2), plate_to_image)
    illum_t = _shift(illum, x0, y0, (tcw, tch), cv2.BORDER_REPLICATE)
    occ = _shift(occ_plate, x0, y0, (tcw, tch), cv2.BORDER_CONSTANT)

    # 2. Макет в своей плоскости (premultiplied alpha → без тёмной каймы).
    tpl = cv2.resize(template_rgba, (tcw, tch), interpolation=cv2.INTER_AREA).astype(np.float32)
    alpha: ImageArray = tpl[..., 3:4] / 255.0
    color: ImageArray = tpl[..., :3]
    if not covers_plate:
        color = add_rim_and_sheen(color, alpha)

    # 3. Освещённость, тени, блики: макет «белый» = TEMPLATE_WHITE.
    gain = np.clip(illum_t / TEMPLATE_WHITE, 0.12, 1.15)[..., None]
    cast = estimate_color_cast(src_plate, illum)
    color = color * gain * cast[None, None, :]

    # 4. Размытие под резкость исходника.
    sharp_src = _laplacian_var(src_gray)
    sigma = match_blur(
        cv2.cvtColor(np.clip(color, 0, 255), cv2.COLOR_BGR2GRAY), sharp_src, min(ch, tch) / 8
    )
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
    alpha = alpha * (1.0 - occ[..., None])

    # 7. Обратно в перспективу кадра.
    to_image = cv2.getPerspectiveTransform(
        _canon_corners(tcw, tch), target_quad.reshape(4, 2).astype(np.float32)
    )
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
    base = image
    if not covers_plate:
        # Макет меньше номера: убираем старый номер и кладём мягкую тень под табличку.
        base = remove_old_plate(image, corners, noise, seed)
        _, target_h = quad_size(target_quad.reshape(4, 2))
        shadow = cv2.GaussianBlur(a[..., 0], (0, 0), max(1.0, target_h * 0.07))
        dy = max(1, round(target_h * 0.05))
        shadow = np.roll(shadow, dy, axis=0)[..., None]
        base = (base.astype(np.float32) * (1.0 - 0.45 * shadow)).astype(np.float32)
    out = warped[..., :3] + base.astype(np.float32) * (1.0 - a)
    result = np.clip(out + 0.5, 0, 255).astype(np.uint8)

    info = OverlayInfo(
        blur_sigma=float(sigma),
        gain_mean=float(gain.mean()),
        color_cast=(float(cast[0]), float(cast[1]), float(cast[2])),
        noise_sigma=float(noise),
        occluded_fraction=float(occ_plate.mean()),
    )
    return result, info
