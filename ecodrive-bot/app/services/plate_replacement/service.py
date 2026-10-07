"""Замена номерной таблички: детекция → проверка уверенности → наложение."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2

from app.services.plate_replacement.detector import PlateDetection, PlateDetector
from app.services.plate_replacement.overlay import FIT_PLATE, OverlayInfo, overlay_plate
from app.utils.types import ImageArray


def load_template(path: Path) -> ImageArray:
    """Загружает прозрачный PNG-макет таблички как BGRA."""
    template = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if template is None:
        raise FileNotFoundError(f"branded plate template not found: {path}")
    if template.ndim == 2:
        template = cv2.cvtColor(template, cv2.COLOR_GRAY2BGRA)
    elif template.shape[2] == 3:
        template = cv2.cvtColor(template, cv2.COLOR_BGR2BGRA)
    return template


@dataclass
class PlateReplacementResult:
    image: ImageArray
    replaced: bool
    confidence: float
    detection: PlateDetection | None = None
    overlay: OverlayInfo | None = None
    candidates: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class PlateReplacer:
    def __init__(
        self,
        template_bgra: ImageArray,
        detector: PlateDetector,
        *,
        confidence_threshold: float = 0.55,
        expand: float = 0.03,
        height_ratio: float = 1.5,
        fit: str = FIT_PLATE,
    ) -> None:
        self.fit = fit
        self.template = template_bgra
        self.detector = detector
        self.threshold = confidence_threshold
        self.expand = expand
        self.height_ratio = height_ratio

    def replace(self, image_bgr: ImageArray) -> PlateReplacementResult:
        detections = self.detector.detect(image_bgr)
        if not detections:
            return PlateReplacementResult(image=image_bgr, replaced=False, confidence=0.0)
        best = detections[0]
        if best.confidence < self.threshold:
            return PlateReplacementResult(
                image=image_bgr,
                replaced=False,
                confidence=best.confidence,
                detection=best,
                candidates=len(detections),
            )
        return self.place(image_bgr, best, candidates=len(detections))

    def place(
        self, image_bgr: ImageArray, detection: PlateDetection, *, candidates: int = 1
    ) -> PlateReplacementResult:
        """Ставит табличку на заданный (уже выбранный) номер."""
        result, info = overlay_plate(
            image_bgr,
            detection.corners,
            self.template,
            expand=self.expand,
            height_ratio=self.height_ratio,
            fit=self.fit,
        )
        return PlateReplacementResult(
            image=result,
            replaced=True,
            confidence=detection.confidence,
            detection=detection,
            overlay=info,
            candidates=candidates,
            metadata={"corners": detection.corners.round(1).tolist(), "method": detection.method},
        )
