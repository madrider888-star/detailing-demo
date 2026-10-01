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


def refine_quad(image: ImageBGR, quad: Quad) -> Quad | None:
    """Уточняет углы: верх/низ — по градиенту, бока — по профилю «светлый фон или
    синяя EU-полоса». Возвращает None, если уточнение ненадёжно."""
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

    def horizontal_edge(center: float) -> tuple[float, float] | None:
        xs, ys = [], []
        band = max(2, int(ph * 0.22))
        for x in np.linspace(left_x + pw * 0.15, right_x - pw * 0.1, 40).astype(int):
            if not 0 <= x < cw:
                continue
            y0, y1 = max(0, int(center - band)), min(ch, int(center + band) + 1)
            column = gy[y0:y1, x]
            if column.size and column.max() > 20:
                xs.append(x)
                ys.append(y0 + int(column.argmax()))
        return _fit_line_y(np.array(xs, float), np.array(ys, float))

    top = horizontal_edge(top_y)
    bottom = horizontal_edge(bottom_y)
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


class ContourPlateDetector:
    def __init__(self, max_side: int = 1280, max_candidates: int = 5) -> None:
        self.max_side = max_side
        self.max_candidates = max_candidates

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
        for binary in self._binary_maps(gray):
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
                if conf <= 0.2:
                    continue
                refined = refine_quad(small, quad)
                if refined is not None:
                    r_conf, r_feats = score_candidate(refined, small, 1.0)
                    # Уточнённые углы принимаем, если «похожесть на номер» заметно не упала
                    # (EU-полоса слегка снижает оценку символов — это нормально).
                    if r_conf >= conf - 0.1:
                        quad, conf, feats = refined, max(conf, r_conf), r_feats
                candidates.append(
                    PlateDetection(
                        corners=(quad / scale).astype(np.float32),
                        confidence=conf,
                        method="contour",
                        features=feats,
                    )
                )
        return _non_max_suppression(candidates)[: self.max_candidates]


def _non_max_suppression(cands: list[PlateDetection], iou: float = 0.4) -> list[PlateDetection]:
    kept: list[PlateDetection] = []
    for cand in sorted(cands, key=lambda c: c.confidence, reverse=True):
        if all(bbox_iou(cand.corners, k.corners) < iou for k in kept):
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
