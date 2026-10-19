"""Детекция номерной таблички классическим компьютерным зрением.

`ContourPlateDetector` не требует нейросети: ищет светлые прямоугольные области с
пропорциями номера, проверяет наличие «символов» внутри и возвращает четыре угла и
уверенность. `OnnxPlateDetector` (необязательный) использует YOLO-модель в формате
ONNX для поиска рамки, а углы уточняет тем же контурным методом.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

from app.services.plate_replacement.geometry import (
    bbox_iou,
    expand_quad,
    is_convex,
    order_corners,
    quad_area,
    quad_size,
)
from app.utils.types import ImageArray, Quad

ImageBGR = ImageArray

# Европейский формат (Украина): 520×112 мм.
EU_ASPECT = 520 / 112
CANON_W, CANON_H = 260, 56
# Кромка над тёмной полосой с флагом слабее, чем над белым полем (≈ 0.3 от неё),
# а переход держатель → тёмный кузов — ≈ 0.08: порог между ними.
EDGE_RUN_MIN = 0.18
REFINE_MAX_GAIN = 0.1  # насколько уточнение углов может поднять уверенность кандидата


@dataclass(frozen=True)
class PlateDetection:
    corners: Quad  # координаты в исходном изображении, TL TR BR BL
    confidence: float
    method: str
    features: dict[str, float]


class PlateDetector(Protocol):
    def detect(self, image: ImageBGR) -> list[PlateDetection]: ...


def _aspect_score(aspect: float) -> float:
    # 1.0 для пропорций EU-номера, плавно падает к 2.0 и 9.0; квадратные таблички (≈2) — 0.4.
    distance = abs(math.log(aspect / EU_ASPECT))
    return max(0.0, 1.0 - distance / math.log(2.4))


def _band(value: float, low: float, high: float, soft: float) -> float:
    if low <= value <= high:
        return 1.0
    edge = low if value < low else high
    return max(0.0, 1.0 - abs(value - edge) / soft)


def rectify(image: ImageBGR, quad: Quad, size: tuple[int, int] = (CANON_W, CANON_H)) -> ImageBGR:
    w, h = size
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(quad.astype(np.float32), dst)
    return cv2.warpPerspective(
        image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )


def character_features(plate: ImageBGR) -> dict[str, float]:
    """Признаки «это номер»: светлый фон, тёмные символы нужной высоты в ряд."""
    gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # Не учитываем край таблички (рамка/бампер) — 6 % по вертикали и 3 % по горизонтали.
    my, mx = max(1, int(h * 0.06)), max(1, int(w * 0.03))
    inner = binary[my : h - my, mx : w - mx]
    dark_ratio = float(inner.mean() / 255)
    n, _, stats, _ = cv2.connectedComponentsWithStats(inner, connectivity=8)
    chars = []
    for i in range(1, n):
        x, y, cw, ch, area = stats[i]
        if 0.35 * h <= ch <= 0.95 * h and 0.015 * w <= cw <= 0.16 * w and area >= 0.15 * cw * ch:
            chars.append((x, y, cw, ch))
    alignment = 0.0
    if len(chars) >= 3:
        centers = np.array([y + ch / 2 for _, y, _, ch in chars])
        heights = np.array([ch for *_, ch in chars], dtype=np.float64)
        alignment = float(
            max(0.0, 1.0 - centers.std() / (0.25 * h))
            * max(0.0, 1.0 - heights.std() / heights.mean())
        )
    contrast = float(gray.std())
    return {
        "chars": float(len(chars)),
        "dark_ratio": dark_ratio,
        "alignment": alignment,
        "contrast": contrast,
        "brightness": float(np.percentile(gray, 75)),
    }


def score_candidate(
    quad: Quad, image: ImageBGR, contour_fill: float
) -> tuple[float, dict[str, float]]:
    img_h, img_w = image.shape[:2]
    width, height = quad_size(quad)
    if height < 8 or width < 30:
        return 0.0, {}
    aspect = width / height
    rel_area = quad_area(quad) / (img_w * img_h)
    feats = character_features(rectify(image, quad))
    s_aspect = _aspect_score(aspect)
    s_area = _band(rel_area, 0.0008, 0.08, 0.04)
    s_fill = _band(contour_fill, 0.8, 1.0, 0.3)
    s_chars = min(1.0, feats["chars"] / 5.0) * (0.5 + 0.5 * feats["alignment"])
    s_dark = _band(feats["dark_ratio"], 0.08, 0.45, 0.15)
    s_contrast = _band(feats["contrast"], 35, 200, 25)
    s_bright = _band(feats["brightness"], 120, 255, 70)
    confidence = (
        0.20 * s_aspect
        + 0.10 * s_fill
        + 0.35 * s_chars
        + 0.15 * s_dark
        + 0.10 * s_contrast
        + 0.10 * s_bright
    ) * (1.0 if s_area > 0 else 0.0)
    feats.update(
        aspect=aspect, rel_area=rel_area, fill=contour_fill, s_aspect=s_aspect, s_chars=s_chars
    )
    return float(confidence), feats


def _quad_from_contour(contour: ImageArray) -> Quad:
    peri = cv2.arcLength(contour, True)
    for eps in (0.02, 0.03, 0.045):
        approx = cv2.approxPolyDP(contour, eps * peri, True)
        if len(approx) == 4:
            quad = order_corners(approx.reshape(4, 2))
            if is_convex(quad):
                return quad
    return order_corners(cv2.boxPoints(cv2.minAreaRect(contour)))


def _fit_line_y(xs: ImageArray, ys: ImageArray) -> tuple[float, float] | None:
    """Робастная прямая y = a·x + b."""
    if len(xs) < 5:
        return None
    pts = np.column_stack([xs, ys]).astype(np.float32)
    vx, vy, x0, y0 = cv2.fitLine(pts, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
    if abs(vx) < 1e-6:
        return None
    a = float(vy / vx)
    return a, float(y0 - a * x0)


def _fit_line_x(ys: ImageArray, xs: ImageArray) -> tuple[float, float] | None:
    """Робастная прямая x = c·y + d (почти вертикальные края)."""
    return _fit_line_y(ys, xs)


def _strip_like(
    canon: ImageBGR,
    top: tuple[float, float],
    bottom: tuple[float, float],
    x_a: float,
    x_b: float,
) -> bool:
    """Похожа ли зона между x_a и x_b на полосу номера: синяя EU-полоса, либо тёмная
    полоса с флагом сверху и светлыми буквами «UA» снизу. Держатель и бампер — нет."""
    x0, x1 = sorted((round(x_a), round(x_b)))
    xc = (x0 + x1) / 2
    y0 = round(top[0] * xc + top[1])
    y1 = round(bottom[0] * xc + bottom[1])
    h = y1 - y0
    if x1 - x0 < 2 or h < 6:
        return False
    zone = canon[y0 + round(h * 0.12) : y1 - round(h * 0.12), x0:x1]
    if zone.size == 0:
        return False
    hsv = cv2.cvtColor(zone, cv2.COLOR_BGR2HSV)
    sat = hsv[..., 1] >= 70
    gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)
    half = gray.shape[0] // 2
    letters = float((gray[half:] >= 150).mean()) if half else 0.0
    colored_top = float(sat[:half].mean()) if half else 0.0
    return bool(float(sat.mean()) >= 0.5 or colored_top >= 0.08 or letters >= 0.04)


def edge_run_side(
    gy: ImageArray,
    gx: ImageArray,
    top: tuple[float, float],
    bottom: tuple[float, float],
    left_x: float,
    right_x: float,
    direction: int,
    canon: ImageBGR | None = None,
) -> tuple[float, float] | None:
    """Боковой край номера x = c·y + d — там, где кончаются его верхняя и нижняя кромки.

    Кромка таблички идёт и над тёмной полосой с флагом и «UA», а на держателе и кузове
    пропадает, поэтому край не зависит от цвета полосы. Затем край подтягивается к
    самому сильному вертикальному перепаду рядом (кант таблички / держатель).
    """
    ch, cw = gy.shape
    pw = right_x - left_x
    center = int((left_x + right_x) / 2)

    def strength(line: tuple[float, float], x: int) -> float:
        y = round(line[0] * x + line[1])
        y0, y1 = max(0, y - 2), min(ch, y + 3)
        return float(gy[y0:y1, x].max()) if y1 > y0 else 0.0

    def run_end(line: tuple[float, float]) -> float | None:
        inner = range(int(left_x + pw * 0.25), int(right_x - pw * 0.25))
        values = [strength(line, x) for x in inner if 0 <= x < cw]
        if not values:
            return None
        ref = float(np.median(values))
        if ref < 15:
            return None
        limit = (left_x if direction < 0 else right_x) + direction * pw * 0.3
        max_misses = max(3, round(pw * 0.015))
        x, misses, last_good = center, 0, center
        while 1 <= x < cw - 1 and (x - limit) * direction <= 0:
            if strength(line, x) >= EDGE_RUN_MIN * ref:
                misses, last_good = 0, x
            else:
                misses += 1
                if misses > max_misses:
                    break
            x += direction
        return last_good + 0.5 * direction

    end_top, end_bottom = run_end(top), run_end(bottom)
    if end_top is None or end_bottom is None:
        return None
    gap = abs(end_top - end_bottom)
    if gap > 0.1 * pw:
        # Одна кромка прервалась раньше (мелкий номер, блик, символы у края). Разница
        # не больше полосы с флагом (≈ 10 % длины) — берём дальнюю, иначе дальняя
        # кромка ушла на держатель или бампер — берём ближнюю.
        outer = min(end_top, end_bottom) if direction < 0 else max(end_top, end_bottom)
        inner = max(end_top, end_bottom) if direction < 0 else min(end_top, end_bottom)
        strip = (
            canon is not None and gap <= 0.16 * pw and _strip_like(canon, top, bottom, inner, outer)
        )
        end_top = end_bottom = outer if strip else inner

    def y_top(x: float) -> float:
        return top[0] * x + top[1]

    def y_bottom(x: float) -> float:
        return bottom[0] * x + bottom[1]

    def segment_score(xt: float, xb: float) -> float:
        yt, yb = y_top(xt), y_bottom(xb)
        total, n = 0.0, 0
        for t in np.linspace(0.15, 0.85, 12):
            x, y = round(xt + t * (xb - xt)), round(yt + t * (yb - yt))
            if 0 <= x < cw and 0 <= y < ch:
                total += float(gx[y, max(0, x - 1) : x + 2].max())
                n += 1
        return total / n if n else 0.0

    reach = max(2, round(pw * 0.03))
    best = (segment_score(end_top, end_bottom), end_top, end_bottom)
    # Край сдвигаем почти параллельно: наклон боковой стороны задают концы кромок.
    for dt in range(-reach, reach + 1):
        for db in range(dt - 2, dt + 3):
            score = segment_score(end_top + dt, end_bottom + db)
            if score > best[0]:
                best = (score, end_top + dt, end_bottom + db)
    _, xt, xb = best
    yt, yb = y_top(xt), y_bottom(xb)
    if abs(yb - yt) < 1:
        return None
    c = (xb - xt) / (yb - yt)
    return c, xt - c * yt


def edge_support(image: ImageBGR, quad: Quad) -> float:
    """Насколько стороны четырёхугольника лежат на реальных перепадах яркости."""
    h, w = image.shape[:2]
    x0, y0 = np.floor(quad.min(axis=0)).astype(int) - 4
    x1, y1 = np.ceil(quad.max(axis=0)).astype(int) + 5
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return 0.0
    gray = cv2.GaussianBlur(
        cv2.cvtColor(image[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32), (3, 3), 0
    )
    mag = cv2.magnitude(cv2.Sobel(gray, cv2.CV_32F, 1, 0), cv2.Sobel(gray, cv2.CV_32F, 0, 1))
    local = quad - np.array([x0, y0], dtype=np.float32)
    sides = []
    for i in range(4):
        a, b = local[i], local[(i + 1) % 4]
        pts = [a + t * (b - a) for t in np.linspace(0.1, 0.9, 24)]
        vals = [
            float(mag[max(0, int(y) - 1) : int(y) + 2, max(0, int(x) - 1) : int(x) + 2].max())
            for x, y in pts
            if 0 <= int(x) < mag.shape[1] and 0 <= int(y) < mag.shape[0]
        ]
        sides.append(float(np.median(vals)) if vals else 0.0)
    # Самая слабая сторона важнее средней: один «съехавший» край и есть кривая табличка.
    return 0.5 * min(sides) + 0.5 * float(np.mean(sides))


def refine_quad(image: ImageBGR, quad: Quad) -> Quad | None:
    """Уточняет углы номера, начиная с грубого контура и с его описанного прямоугольника.

    Грубый контур бывает «сломан» (например, без тёмной полосы с флагом) — тогда
    верхний край ищется наискосок через символы. Каждый старт уточняется дважды;
    побеждает вариант, стороны которого лучше всего лежат на реальных краях.
    """
    starts = [quad, order_corners(cv2.boxPoints(cv2.minAreaRect(quad.astype(np.float32))))]
    results: list[Quad] = []
    for start in starts:
        for outermost in (False, True):
            current = _refine_once(image, start, outermost=outermost)
            if current is None:
                continue
            again = _refine_once(image, current, outermost=outermost)
            results.append(current if again is None else again)
    if not results:
        return None
    # Граница полосы с флагом и белого поля контрастнее, чем полосы и чёрного держателя,
    # поэтому «самый сильный край» часто внутренний. Из вариантов, уверенно лежащих на
    # краях, берём самый большой — внешний контур номера.
    supports = [edge_support(image, q) for q in results]
    good = [q for q, sup in zip(results, supports, strict=True) if sup >= 0.6 * max(supports)]
    return max(good, key=quad_area)


def _refine_once(image: ImageBGR, quad: Quad, *, outermost: bool = False) -> Quad | None:
    """Уточняет углы: верх/низ — по градиенту, бока — по концам верхней и нижней кромки
    (запасной вариант — профиль «светлый фон или синяя EU-полоса»).

    `outermost` — верх/низ ищутся в широкой полосе и берётся самый внешний сильный
    перепад: кант таблички, а не верх символов, если грубый контур съехал внутрь.
    Возвращает None, если уточнение ненадёжно."""
    width, height = quad_size(quad)
    if width < 30 or height < 8:
        return None
    outer = expand_quad(quad, 0.4, 1.0)
    cw = 480
    ch = max(40, round(cw * quad_size(outer)[1] / max(quad_size(outer)[0], 1.0)))
    dst = np.array([[0, 0], [cw - 1, 0], [cw - 1, ch - 1], [0, ch - 1]], dtype=np.float32)
    to_canon = cv2.getPerspectiveTransform(outer, dst)
    canon = cv2.warpPerspective(
        image, to_canon, (cw, ch), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE
    )
    rough = cv2.perspectiveTransform(quad.reshape(1, 4, 2), to_canon).reshape(4, 2)
    left_x, right_x = (rough[0, 0] + rough[3, 0]) / 2, (rough[1, 0] + rough[2, 0]) / 2
    top_y, bottom_y = (rough[0, 1] + rough[1, 1]) / 2, (rough[2, 1] + rough[3, 1]) / 2
    pw, ph = right_x - left_x, bottom_y - top_y
    if pw < 20 or ph < 6:
        return None

    gray = cv2.GaussianBlur(cv2.cvtColor(canon, cv2.COLOR_BGR2GRAY), (3, 3), 0).astype(np.float32)
    gy = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))

    def horizontal_edge(center: float, outward: int) -> tuple[float, float] | None:
        xs, ys = [], []
        band = max(3, int(ph * 0.4)) if outermost else max(2, int(ph * 0.22))
        for x in np.linspace(left_x + pw * 0.15, right_x - pw * 0.1, 40).astype(int):
            if not 0 <= x < cw:
                continue
            y0, y1 = max(0, int(center - band)), min(ch, int(center + band) + 1)
            column = gy[y0:y1, x]
            if not column.size or column.max() <= 20:
                continue
            best = int(column.argmax())
            if outermost:
                strong = np.flatnonzero(column >= 0.5 * column.max())
                best = int(strong.min() if outward < 0 else strong.max())
            xs.append(x)
            ys.append(y0 + best)
        return _fit_line_y(np.array(xs, float), np.array(ys, float))

    top = horizontal_edge(top_y, -1)
    bottom = horizontal_edge(bottom_y, +1)
    if top is None or bottom is None:
        return None

    hsv = cv2.cvtColor(canon, cv2.COLOR_BGR2HSV)
    blue = (hsv[..., 0] >= 95) & (hsv[..., 0] <= 130) & (hsv[..., 1] >= 80) & (hsv[..., 2] >= 40)
    inner = gray[
        int(top_y + ph * 0.2) : int(bottom_y - ph * 0.2),
        int(left_x + pw * 0.3) : int(right_x - pw * 0.3),
    ]
    if inner.size == 0:
        return None
    bright_thr = 0.75 * float(np.percentile(inner, 80))
    plate_like = (gray >= bright_thr) | blue

    def side_edge(direction: int) -> tuple[float, float] | None:
        """Идём от центра наружу по линиям, параллельным верхнему/нижнему краю,
        в полях таблички над и под символами; останавливаемся на 4 «чужих» пикселях."""
        ta, tb = top
        ba, bb = bottom
        xs, ys = [], []
        center = int((left_x + right_x) / 2)
        limit = (left_x if direction < 0 else right_x) + direction * pw * 0.15
        for frac in (0.07, 0.1, 0.13, 0.87, 0.9, 0.93):
            x, misses, last_good = center, 0, center
            while 0 <= x < cw and (x - limit) * direction <= 0:
                y_top, y_bottom = ta * x + tb, ba * x + bb
                y = round(y_top + frac * (y_bottom - y_top))
                if 1 <= y < ch - 1 and plate_like[y - 1 : y + 2, x].mean() >= 0.5:
                    misses, last_good = 0, x
                else:
                    misses += 1
                    if misses >= 4:
                        break
                x += direction
            y_top, y_bottom = ta * last_good + tb, ba * last_good + bb
            xs.append(last_good + 0.5 * direction)
            ys.append(y_top + frac * (y_bottom - y_top))
        xs_arr, ys_arr = np.array(xs, float), np.array(ys, float)
        line = _fit_line_x(ys_arr, xs_arr)
        if line is None:
            return None
        residual = np.abs(line[0] * ys_arr + line[1] - xs_arr)
        if residual.max() > 0.04 * pw:  # точки края не ложатся на прямую — ненадёжно
            return None
        return line

    # Кромку ищем по цвету, а не только по яркости: синяя EU-полоса на кузове близкой
    # яркости в сером почти не видна.
    color = cv2.GaussianBlur(canon, (3, 3), 0).astype(np.float32)
    gy_c = np.abs(cv2.Sobel(color, cv2.CV_32F, 0, 1, ksize=3)).max(axis=2)
    gx_c = np.abs(cv2.Sobel(color, cv2.CV_32F, 1, 0, ksize=3)).max(axis=2)
    left = edge_run_side(gy_c, gx_c, top, bottom, left_x, right_x, -1, canon)
    right = edge_run_side(gy_c, gx_c, top, bottom, left_x, right_x, +1, canon)
    if left is None or right is None:
        # Кромка номера не читается — прежний способ: по светлому фону и синей полосе.
        left = side_edge(-1)
        right = side_edge(+1)
    if left is None or right is None:
        return None

    def intersect(h_line: tuple[float, float], v_line: tuple[float, float]) -> tuple[float, float]:
        a, b = h_line
        c, d = v_line
        y = (a * d + b) / (1 - a * c)
        return c * y + d, y

    pts = np.array(
        [
            intersect(top, left),
            intersect(top, right),
            intersect(bottom, right),
            intersect(bottom, left),
        ],
        dtype=np.float32,
    )
    refined = cv2.perspectiveTransform(pts.reshape(1, 4, 2), np.linalg.inv(to_canon)).reshape(4, 2)
    refined = order_corners(refined)
    ratio = quad_area(refined) / max(quad_area(quad), 1.0)
    if not is_convex(refined) or not 0.6 <= ratio <= 1.6:
        return None
    return refined


def color_plate_quad(image: ImageBGR, rough: Quad) -> Quad | None:
    """Точные 4 угла цветной таблички по исходному кадру: маска того же цвета в окрестности
    грубого контура, внешний контур, четырёхугольник по нему."""
    h, w = image.shape[:2]
    x0, y0 = np.floor(rough.min(axis=0)).astype(int)
    x1, y1 = np.ceil(rough.max(axis=0)).astype(int)
    pad_x, pad_y = max(4, (x1 - x0) // 5), max(4, (y1 - y0) // 3)
    x0, y0 = max(0, x0 - pad_x), max(0, y0 - pad_y)
    x1, y1 = min(w, x1 + pad_x), min(h, y1 + pad_y)
    roi = image[y0:y1, x0:x1]
    if roi.size == 0:
        return None
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    center = np.round(rough.mean(axis=0) - [x0, y0]).astype(int)
    inner = hsv[
        max(0, center[1] - 2) : center[1] + 3, max(0, center[0] - (x1 - x0) // 4) : center[0]
    ]
    if inner.size == 0:
        return None
    hue = float(np.median(inner[..., 0]))
    diff = np.abs(hsv[..., 0].astype(np.int16) - round(hue))
    diff = np.minimum(diff, 180 - diff)
    mask = ((diff <= 12) & (hsv[..., 1] >= 70) & (hsv[..., 2] >= 50)).astype(np.uint8) * 255
    k = max(3, (y1 - y0) // 6) | 1
    mask = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    )
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < 0.3 * quad_area(rough - np.array([x0, y0], np.float32)):
        return None
    hull = cv2.convexHull(contour)
    quad = _quad_from_contour(hull)
    if not is_convex(quad):
        return None
    return (quad + np.array([x0, y0], dtype=np.float32)).astype(np.float32)


def color_plate_confidence(feats: dict[str, float], fill: float) -> float:
    """Сплошная цветная прямоугольная область с символами — номер, даже если в кадре он
    из-за ракурса «короче» EU-пропорций (жёлтая заглушка 懂车帝 сбоку ≈ 2:1)."""
    # Иероглифы (懂车帝) распадаются на штрихи и «символами» не считаются — поэтому
    # проверяем просто наличие тёмной надписи/логотипа: ровная деталь кузова её не имеет.
    dark = feats.get("dark_ratio", 0.0)
    if not 0.08 <= dark <= 0.55 or feats.get("contrast", 0.0) < 25:
        return 0.0
    if not 1.3 <= feats.get("aspect", 0.0) <= 6.0:
        return 0.0
    content = min(1.0, feats.get("chars", 0.0) / 4.0)
    return 0.6 + 0.2 * _band(fill, 0.8, 1.0, 0.3) + 0.1 * content


class ContourPlateDetector:
    def __init__(self, max_side: int = 1280, max_candidates: int = 5) -> None:
        self.max_side = max_side
        self.max_candidates = max_candidates

    def _color_maps(self, image: ImageBGR) -> list[ImageArray]:
        """Цветные таблички целиком: жёлтая заглушка 懂车帝 / жёлтый номер, синий и
        зелёный китайские. Без этого детектор видит в них только строку символов."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        masks = [
            (h >= 15) & (h <= 38) & (s >= 90) & (v >= 90),  # жёлтый
            (h >= 100) & (h <= 125) & (s >= 110) & (v >= 60),  # синий
            (h >= 40) & (h <= 85) & (s >= 50) & (v >= 90),  # зелёный (электромобили)
        ]
        ih, iw = image.shape[:2]
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, iw // 80), max(3, ih // 80)))
        return [
            cv2.morphologyEx(m.astype(np.uint8) * 255, cv2.MORPH_CLOSE, kernel, iterations=2)
            for m in masks
        ]

    def _binary_maps(self, gray: ImageArray) -> list[ImageArray]:
        h, w = gray.shape
        maps: list[ImageArray] = []
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        maps.append(otsu)
        block = max(31, (min(h, w) // 12) | 1)
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block, -8
        )
        maps.append(adaptive)
        _, bright = cv2.threshold(gray, int(np.percentile(gray, 85)), 255, cv2.THRESH_BINARY)
        maps.append(bright)
        closed: list[ImageArray] = []
        kx, ky = max(3, w // 60), max(3, h // 90)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kx, ky))
        for m in maps:
            # Закрытие заполняет тёмные символы внутри светлой таблички.
            closed.append(cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2))
        edges = cv2.Canny(cv2.bilateralFilter(gray, 7, 50, 50), 50, 150)
        closed.append(cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1))
        return closed

    def detect(self, image: ImageBGR) -> list[PlateDetection]:
        h, w = image.shape[:2]
        scale = min(1.0, self.max_side / max(h, w))
        small = (
            cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
            if scale < 1.0
            else image
        )
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        sh, sw = gray.shape
        candidates: list[PlateDetection] = []
        gray_maps, color_maps = self._binary_maps(gray), self._color_maps(small)
        for index, binary in enumerate(gray_maps + color_maps):
            colored = index >= len(gray_maps)
            contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 0.0006 * sw * sh or area > 0.1 * sw * sh:
                    continue
                _, _, bw, bh = cv2.boundingRect(contour)
                if bw < 1.5 * bh or bw > 10 * bh:
                    continue
                quad = _quad_from_contour(contour)
                q_area = quad_area(quad)
                if q_area <= 0:
                    continue
                fill = min(1.0, area / q_area)
                conf, feats = score_candidate(quad, small, fill)
                if colored:
                    # Цветная табличка: граница цвета и есть край номера (жёлтое на белом
                    # кузове видно точно), уточнять по яркости не нужно — оно «съезжает»
                    # на тень и описанный прямоугольник.
                    exact = color_plate_quad(image, (quad / scale).astype(np.float32))
                    if exact is not None:
                        quad = exact * scale
                        conf, feats = score_candidate(quad, small, fill)
                        conf = max(conf, color_plate_confidence(feats, fill))
                        if conf > 0.2:
                            candidates.append(
                                PlateDetection(
                                    corners=exact,
                                    confidence=conf,
                                    method="color",
                                    features=feats,
                                )
                            )
                    continue
                if conf <= 0.2:
                    continue
                # Углы уточняем по исходному кадру: на уменьшенной копии номер под углом
                # занимает несколько десятков пикселей и край «гуляет».
                refined_full = refine_quad(image, (quad / scale).astype(np.float32))
                refined = None if refined_full is None else (refined_full * scale)
                if refined is not None:
                    r_conf, r_feats = score_candidate(refined, small, 1.0)
                    # Уточнённые углы принимаем, если «похожесть на номер» заметно не упала
                    # (EU-полоса слегка снижает оценку символов — это нормально).
                    # Уточнение исправляет геометрию, но не доказывает, что это номер:
                    # текстура (гравий, листва) в «удачной» рамке набирает ложные символы.
                    if r_conf >= conf - 0.1:
                        boosted = min(max(conf, r_conf), conf + REFINE_MAX_GAIN)
                        quad, conf, feats = refined, boosted, r_feats
                candidates.append(
                    PlateDetection(
                        corners=(quad / scale).astype(np.float32),
                        confidence=conf,
                        method="contour",
                        features=feats,
                    )
                )
        return _non_max_suppression(candidates)[: self.max_candidates]


def _bbox_containment(a: Quad, b: Quad) -> float:
    """Какая доля меньшей рамки лежит внутри большей (по описанным прямоугольникам)."""
    ax0, ay0 = a.min(axis=0)
    ax1, ay1 = a.max(axis=0)
    bx0, by0 = b.min(axis=0)
    bx1, by1 = b.max(axis=0)
    iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0.0, min(ay1, by1) - max(ay0, by0))
    smaller = min((ax1 - ax0) * (ay1 - ay0), (bx1 - bx0) * (by1 - by0))
    return float(iw * ih / smaller) if smaller > 0 else 0.0


def _non_max_suppression(
    cands: list[PlateDetection], iou: float = 0.4, containment: float = 0.7
) -> list[PlateDetection]:
    """Убирает повторы и вложенные рамки: строка символов внутри таблички или кусок
    бампера вокруг неё не должны соперничать с самой табличкой (vision-модель, видя
    вложенные рамки, выбирала внутреннюю — табличка ложилась на надпись)."""
    kept: list[PlateDetection] = []
    for cand in sorted(cands, key=lambda c: c.confidence, reverse=True):
        if all(
            bbox_iou(cand.corners, k.corners) < iou
            and _bbox_containment(cand.corners, k.corners) < containment
            for k in kept
        ):
            kept.append(cand)
    return kept


class OnnxPlateDetector:
    """YOLOv8/YOLO11 single-class ONNX-модель номеров (выход [1, 5, N]).

    Модель находит рамку номера; точные углы уточняются контурным детектором внутри
    рамки. Если уточнение не удалось — используются углы рамки.
    """

    def __init__(self, model_path: Path, input_size: int = 640, min_score: float = 0.35) -> None:
        self.net = cv2.dnn.readNetFromONNX(str(model_path))
        self.input_size = input_size
        self.min_score = min_score
        self.refiner = ContourPlateDetector(max_side=640)

    def detect(self, image: ImageBGR) -> list[PlateDetection]:
        h, w = image.shape[:2]
        blob = cv2.dnn.blobFromImage(
            image, 1 / 255.0, (self.input_size, self.input_size), swapRB=True, crop=False
        )
        self.net.setInput(blob)
        output = self.net.forward()
        boxes = parse_yolo_output(output, (w, h), self.input_size, self.min_score)
        detections: list[PlateDetection] = []
        for (x0, y0, x1, y1), score in boxes:
            pad_x, pad_y = (x1 - x0) * 0.15, (y1 - y0) * 0.3
            rx0, ry0 = max(0, int(x0 - pad_x)), max(0, int(y0 - pad_y))
            rx1, ry1 = min(w, int(x1 + pad_x)), min(h, int(y1 + pad_y))
            roi = image[ry0:ry1, rx0:rx1]
            refined = self.refiner.detect(roi) if roi.size else []
            if refined and refined[0].confidence > 0.3:
                corners = refined[0].corners + np.array([rx0, ry0], dtype=np.float32)
                conf = 0.6 * score + 0.4 * refined[0].confidence
            else:
                corners = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.float32)
                conf = score * 0.8
            detections.append(PlateDetection(corners, float(conf), "onnx", {"score": score}))
        return _non_max_suppression(detections)


def parse_yolo_output(
    output: ImageArray, image_size: tuple[int, int], input_size: int, min_score: float
) -> list[tuple[tuple[float, float, float, float], float]]:
    """Разбор выхода YOLO [1, 4+C, N] → рамки в координатах изображения."""
    # Экспорт Ultralytics: [1, 4+C, N] — каналы первыми; транспонируем в [N, 4+C].
    preds = np.squeeze(output, axis=0).T
    w, h = image_size
    sx, sy = w / input_size, h / input_size
    result: list[tuple[tuple[float, float, float, float], float]] = []
    for row in preds:
        score = float(row[4:].max())
        if score < min_score:
            continue
        cx, cy, bw, bh = (float(v) for v in row[:4])
        box = ((cx - bw / 2) * sx, (cy - bh / 2) * sy, (cx + bw / 2) * sx, (cy + bh / 2) * sy)
        result.append((box, score))
    result.sort(key=lambda item: item[1], reverse=True)
    return result[:10]


def create_detector(model_path: Path | None) -> PlateDetector:
    if model_path is not None and model_path.is_file():
        return OnnxPlateDetector(model_path)
    return ContourPlateDetector()
