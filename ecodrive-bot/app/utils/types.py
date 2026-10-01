"""Типы массивов изображений.

Стабы OpenCV возвращают ndarray с обобщённым dtype, поэтому на границах с cv2
используем `NDArray[Any]`; фактический dtype описан в докстрингах функций.
"""

from typing import Any

from numpy.typing import NDArray

ImageArray = NDArray[Any]  # BGR/BGRA uint8 или float32 по контексту
"""Изображение в формате OpenCV."""

Quad = NDArray[Any]  # (4, 2) float32: TL, TR, BR, BL
"""Четырёхугольник номерной таблички."""
