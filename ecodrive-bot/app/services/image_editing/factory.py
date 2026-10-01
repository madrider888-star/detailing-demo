"""Выбор провайдера по операции и настройкам."""

from __future__ import annotations

from app.core.config import Settings
from app.core.enums import Operation
from app.services.image_editing.base import ImageEditingProvider
from app.services.image_editing.mock import MockImageProvider


class ProviderRegistry:
    """Хранит провайдеры и отдаёт подходящий для операции."""

    def __init__(self, default: ImageEditingProvider, plate: ImageEditingProvider) -> None:
        self.default = default
        self.plate = plate

    def for_operation(self, operation: Operation) -> ImageEditingProvider:
        return self.plate if operation is Operation.PLATE else self.default

    def name_for(self, operation: Operation) -> str:
        return self.for_operation(operation).name

    async def aclose(self) -> None:
        await self.default.aclose()
        if self.plate is not self.default:
            await self.plate.aclose()


def build_default_provider(settings: Settings) -> ImageEditingProvider:
    if settings.image_provider == "openai":
        from app.services.image_editing.openai_provider import OpenAIImageEditProvider

        return OpenAIImageEditProvider(
            api_key=settings.openai_api_key.get_secret_value(),
            base_url=settings.openai_base_url,
            model=settings.openai_image_model,
            quality=settings.openai_image_quality,
            input_fidelity=settings.openai_input_fidelity or None,
            timeout=settings.provider_timeout_seconds,
            max_retries=settings.provider_max_retries,
        )
    return MockImageProvider()


def build_plate_provider(settings: Settings) -> ImageEditingProvider:
    if settings.plate_provider == "opencv":
        from app.services.image_editing.opencv_plate import OpenCVPlateProvider
        from app.services.plate_replacement.detector import create_detector
        from app.services.plate_replacement.service import PlateReplacer, load_template

        replacer = PlateReplacer(
            load_template(settings.branded_plate_path),
            create_detector(settings.plate_detector_model_path),
            confidence_threshold=settings.plate_confidence_threshold,
        )
        return OpenCVPlateProvider(replacer)
    return MockImageProvider()


def build_registry(settings: Settings) -> ProviderRegistry:
    return ProviderRegistry(build_default_provider(settings), build_plate_provider(settings))
