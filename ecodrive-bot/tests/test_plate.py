"""Детекция номера и перспективное наложение фирменной таблички."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from app.core.config import Settings
from app.services.plate_replacement.detector import ContourPlateDetector, parse_yolo_output, rectify
from app.services.plate_replacement.geometry import expand_quad, order_corners
from app.services.plate_replacement.overlay import overlay_plate
from app.services.plate_replacement.service import PlateReplacer, load_template
from tests.synthetic import make_scene

SCENES = {
    "frontal": None,
    "tilted": np.array([[400, 560], [700, 600], [698, 668], [398, 620]], np.float32),
    "perspective": np.array([[560, 590], [800, 604], [802, 664], [562, 662]], np.float32),
}


@pytest.fixture(scope="module")
def template() -> np.ndarray:
    return load_template(Settings(_env_file=None).branded_plate_path)  # type: ignore[call-arg]


def _ncc(a: np.ndarray, b: np.ndarray) -> float:
    a = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32)
    b = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-6))


def test_order_corners_is_stable() -> None:
    pts = np.array([[10, 50], [100, 5], [0, 0], [110, 60]], np.float32)
    ordered = order_corners(pts)
    assert ordered.tolist() == [[0, 0], [100, 5], [110, 60], [10, 50]]


@pytest.mark.parametrize("name", list(SCENES))
def test_detector_finds_plate_corners(name: str) -> None:
    scene, truth = make_scene(SCENES[name])
    detections = ContourPlateDetector().detect(scene)
    assert detections, "plate not detected"
    best = detections[0]
    assert best.confidence > 0.8
    assert np.abs(best.corners - truth).max() < 6.0


def test_detector_low_confidence_without_plate() -> None:
    blank = np.full((700, 1000, 3), 128, np.uint8)
    cv2.rectangle(blank, (100, 100), (900, 600), (40, 40, 140), -1)
    detections = ContourPlateDetector().detect(blank)
    assert not detections or detections[0].confidence < 0.55


@pytest.mark.parametrize("name", list(SCENES))
def test_overlay_follows_perspective(name: str, template: np.ndarray) -> None:
    scene, truth = make_scene(SCENES[name])
    result, info = overlay_plate(scene, truth, template, expand=0.0)
    # Выпрямляем область по тем же углам — должен получиться наш макет.
    rect = rectify(result, truth, (520, 112))
    expected = cv2.resize(template[..., :3], (520, 112), interpolation=cv2.INTER_AREA)
    assert _ncc(rect, expected) > 0.85
    # Исходный номер больше не виден: корреляция с ним низкая.
    original = rectify(scene, truth, (520, 112))
    assert _ncc(rect, original) < 0.5
    assert info.occluded_fraction < 0.05


def test_overlay_does_not_touch_pixels_outside_plate(template: np.ndarray) -> None:
    scene, truth = make_scene()
    result, _ = overlay_plate(scene, truth, template, expand=0.03)
    mask = np.zeros(scene.shape[:2], np.uint8)
    cv2.fillConvexPoly(mask, expand_quad(truth, 0.1, 0.2).astype(np.int32), 255)
    outside = mask == 0
    assert np.array_equal(result[outside], scene[outside])


def test_overlay_matches_shadow_and_blur(template: np.ndarray) -> None:
    bright, truth = make_scene(shade=1.0)
    dark, _ = make_scene(shade=0.55, blur=1.6)
    out_bright, info_bright = overlay_plate(bright, truth, template)
    out_dark, info_dark = overlay_plate(dark, truth, template)
    lum_bright = rectify(out_bright, truth).mean()
    lum_dark = rectify(out_dark, truth).mean()
    # Табличка в тени темнее и размыта сильнее — как исходный номер.
    assert lum_dark < lum_bright * 0.75
    assert info_dark.blur_sigma > info_bright.blur_sigma
    assert info_dark.gain_mean < info_bright.gain_mean


def test_overlay_keeps_occluding_frame(template: np.ndarray) -> None:
    scene, truth = make_scene()
    # Тёмная планка рамки перекрывает нижнюю часть номера.
    tl, tr, br, bl = truth
    bar = np.array(
        [
            bl + (tl - bl) * 0.25,
            br + (tr - br) * 0.25,
            br + np.array([0, 6]),
            bl + np.array([0, 6]),
        ],
        np.int32,
    )
    cv2.fillConvexPoly(scene, bar, (25, 25, 25))
    result, info = overlay_plate(scene, truth, template)
    assert info.occluded_fraction > 0.1
    center = bar.mean(axis=0).astype(int)
    assert np.abs(result[center[1], center[0]].astype(int) - 25).max() < 12


def test_replacer_respects_threshold(template: np.ndarray) -> None:
    scene, _ = make_scene()
    detector = ContourPlateDetector()
    assert PlateReplacer(template, detector, confidence_threshold=0.5).replace(scene).replaced
    strict = PlateReplacer(template, detector, confidence_threshold=1.01).replace(scene)
    assert not strict.replaced
    assert np.array_equal(strict.image, scene)


def test_parse_yolo_output() -> None:
    out = np.zeros((1, 5, 3), np.float32)
    out[0, :, 0] = [320, 320, 64, 16, 0.9]  # центр кадра
    out[0, :, 1] = [100, 100, 10, 10, 0.1]  # ниже порога
    boxes = parse_yolo_output(out, (1280, 640), 640, 0.35)
    assert len(boxes) == 1
    (x0, y0, x1, y1), score = boxes[0]
    assert (round(x0), round(y0), round(x1), round(y1)) == (576, 312, 704, 328)
    assert score == pytest.approx(0.9)


def test_colored_original_plate_does_not_tint_overlay(template: np.ndarray) -> None:
    scene, truth = make_scene()
    mask = np.zeros(scene.shape[:2], np.uint8)
    cv2.fillConvexPoly(mask, truth.astype(np.int32), 255)
    yellow = scene.copy()
    yellow[mask > 0] = (yellow[mask > 0] * np.array([0.35, 0.95, 1.0])).astype(np.uint8)
    result, _ = overlay_plate(yellow, truth, template)
    b, _g, r = rectify(result, truth, (520, 112)).reshape(-1, 3).mean(axis=0)
    # Фирменная табличка остаётся нейтральной, а не жёлтой.
    assert b / r > 0.85
