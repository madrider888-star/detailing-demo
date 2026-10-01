"""Геометрия четырёхугольников номерной таблички."""

from __future__ import annotations

import numpy as np

from app.utils.types import ImageArray, Quad


def order_corners(points: ImageArray) -> Quad:
    """Упорядочивает 4 точки: левый верхний, правый верхний, правый нижний, левый нижний."""
    pts = np.asarray(points, dtype=np.float32).reshape(4, 2)
    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    pts = pts[np.argsort(angles)]  # по часовой стрелке в координатах изображения
    # Первой делаем точку с минимальной суммой x+y (левый верхний угол).
    start = int(np.argmin(pts.sum(axis=1)))
    return np.roll(pts, -start, axis=0).astype(np.float32)


def quad_size(quad: Quad) -> tuple[float, float]:
    tl, tr, br, bl = quad
    width = (np.linalg.norm(tr - tl) + np.linalg.norm(br - bl)) / 2
    height = (np.linalg.norm(bl - tl) + np.linalg.norm(br - tr)) / 2
    return float(width), float(height)


def quad_area(quad: Quad) -> float:
    x, y = quad[:, 0], quad[:, 1]
    return float(0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))


def expand_quad(quad: Quad, ratio_x: float, ratio_y: float | None = None) -> Quad:
    """Расширяет четырёхугольник от центра (с учётом наклона сторон)."""
    ratio_y = ratio_x if ratio_y is None else ratio_y
    tl, tr, br, bl = quad.astype(np.float64)
    horizontal = ((tr - tl) + (br - bl)) / 2
    vertical = ((bl - tl) + (br - tr)) / 2
    dx, dy = horizontal * ratio_x / 2, vertical * ratio_y / 2
    out = np.array([tl - dx - dy, tr + dx - dy, br + dx + dy, bl - dx + dy])
    return out.astype(np.float32)


def is_convex(quad: Quad) -> bool:
    signs = []
    for i in range(4):
        a, b, c = quad[i], quad[(i + 1) % 4], quad[(i + 2) % 4]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        signs.append(cross > 0)
    return all(signs) or not any(signs)


def bbox_iou(a: Quad, b: Quad) -> float:
    ax0, ay0 = a.min(axis=0)
    ax1, ay1 = a.max(axis=0)
    bx0, by0 = b.min(axis=0)
    bx1, by1 = b.max(axis=0)
    iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0.0, min(ay1, by1) - max(ay0, by0))
    inter = iw * ih
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return float(inter / union) if union > 0 else 0.0
