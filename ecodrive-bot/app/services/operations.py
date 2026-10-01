"""Каталог операций: пресеты, валидация параметров, сводка и оценка времени.

Параметры задания формируются только здесь, из значений, выбранных кнопками
(или проверенного HEX-кода). Свободный текст пользователя в параметры не попадает.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.core.enums import OPERATION_TITLES, Operation

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")
CUSTOM = "custom"


@dataclass(frozen=True)
class BackgroundPreset:
    title: str
    filename: str
    description: str  # английское описание сцены для промпта


BACKGROUND_PRESETS: dict[str, BackgroundPreset] = {
    "white_studio": BackgroundPreset(
        "⚪ Белая студия",
        "white_studio.jpg",
        "a bright, clean white photo studio cyclorama with soft, even, diffused lighting "
        "and a seamless light-grey floor",
    ),
    "dark_studio": BackgroundPreset(
        "⚫ Тёмная премиальная студия",
        "dark_studio.jpg",
        "a dark premium photo studio with a charcoal seamless backdrop, a soft overhead "
        "light strip and a subtle glossy dark floor",
    ),
    "showroom": BackgroundPreset(
        "🏢 Современный автосалон",
        "showroom.jpg",
        "a modern, bright car dealership showroom with large glass windows, a polished "
        "light floor and neutral architecture, no other cars in frame",
    ),
    "city": BackgroundPreset(
        "🌆 Город",
        "city.jpg",
        "a clean modern city street with contemporary buildings, no people, no other "
        "vehicles in the foreground, natural daylight",
    ),
    "road": BackgroundPreset(
        "🛣 Дорога",
        "road.jpg",
        "an empty asphalt road with open landscape and a clear sky, natural daylight",
    ),
    "neutral_gray": BackgroundPreset(
        "◽ Нейтральный серый",
        "neutral_gray.jpg",
        "a seamless neutral mid-grey studio backdrop with soft even lighting",
    ),
}


@dataclass(frozen=True)
class ColorPreset:
    title: str
    hex: str
    name_en: str


INTERIOR_COLORS: dict[str, ColorPreset] = {
    "black": ColorPreset("⚫ Чёрный", "#1C1C1C", "black"),
    "white": ColorPreset("⚪ Белый", "#F2F0EB", "white"),
    "beige": ColorPreset("🟤 Бежевый", "#D8C3A0", "beige"),
    "brown": ColorPreset("🟫 Коричневый", "#6B4226", "brown"),
    "red": ColorPreset("🔴 Красный", "#B3122E", "red"),
    "burgundy": ColorPreset("🍷 Бордовый", "#6D1A2B", "burgundy"),
    "orange": ColorPreset("🟠 Оранжевый", "#D9631E", "orange"),
}

INTERIOR_PARTS: dict[str, tuple[str, str]] = {
    "seats": ("💺 Сиденья", "seat upholstery"),
    "door_cards": ("🚪 Дверные карты", "leather inserts of the door cards"),
    "armrest": ("🛋 Центральный подлокотник", "the leather centre armrest"),
    "lower_dashboard": ("🎛 Нижняя часть торпедо", "the leather-trimmed lower dashboard"),
    "full_leather": ("✨ Весь кожаный салон", "all leather upholstery surfaces"),
}

WHEEL_SIZES: dict[str, tuple[str, str]] = {
    "keep": ("↔️ Сохранить текущий", "keep exactly the current wheel diameter"),
    "larger": ("⬆️ Визуально больше", "make the rims look about one inch larger in diameter"),
    "smaller": ("⬇️ Визуально меньше", "make the rims look about one inch smaller in diameter"),
}

# Ориентировочное время обработки, секунды.
ETA_SECONDS: dict[Operation, tuple[int, int]] = {
    Operation.PLATE: (10, 30),
    Operation.BACKGROUND: (40, 120),
    Operation.WHEELS: (60, 150),
    Operation.INTERIOR_COLOR: (40, 120),
}


def normalize_hex(value: str) -> str | None:
    match = HEX_RE.match(value.strip())
    if not match:
        return None
    digits = match.group(1)
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return "#" + digits.upper()


class _Params(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PlateParams(_Params):
    pass


class BackgroundParams(_Params):
    background: str
    has_reference: bool = False

    @model_validator(mode="after")
    def _check(self) -> BackgroundParams:
        if self.background != CUSTOM and self.background not in BACKGROUND_PRESETS:
            raise ValueError("unknown background preset")
        if self.background == CUSTOM and not self.has_reference:
            raise ValueError("custom background requires a reference image")
        return self


class WheelParams(_Params):
    size_mode: Literal["keep", "larger", "smaller"] = "keep"


class InteriorParams(_Params):
    color: str
    hex: str
    parts: tuple[str, ...] = Field(min_length=1)

    @field_validator("hex")
    @classmethod
    def _hex(cls, value: str) -> str:
        normalized = normalize_hex(value)
        if normalized is None:
            raise ValueError("invalid HEX")
        return normalized

    @field_validator("parts")
    @classmethod
    def _parts(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        unknown = set(value) - INTERIOR_PARTS.keys()
        if unknown:
            raise ValueError(f"unknown parts: {sorted(unknown)}")
        # «Весь кожаный салон» поглощает остальные пункты.
        if "full_leather" in value:
            return ("full_leather",)
        return tuple(p for p in INTERIOR_PARTS if p in value)

    @model_validator(mode="after")
    def _color(self) -> InteriorParams:
        if self.color != CUSTOM and self.color not in INTERIOR_COLORS:
            raise ValueError("unknown color")
        return self


PARAM_MODELS: dict[Operation, type[_Params]] = {
    Operation.PLATE: PlateParams,
    Operation.BACKGROUND: BackgroundParams,
    Operation.WHEELS: WheelParams,
    Operation.INTERIOR_COLOR: InteriorParams,
}


class OperationParametersError(ValueError):
    pass


def build_parameters(operation: Operation, raw: dict[str, Any]) -> dict[str, Any]:
    """Собирает и валидирует параметры задания из данных диалога."""
    payload: dict[str, Any]
    match operation:
        case Operation.PLATE:
            payload = {}
        case Operation.BACKGROUND:
            payload = {
                "background": raw.get("background"),
                "has_reference": bool(raw.get("reference")),
            }
        case Operation.WHEELS:
            payload = {"size_mode": raw.get("size_mode", "keep")}
        case Operation.INTERIOR_COLOR:
            color = raw.get("color")
            hex_value = (
                raw.get("hex")
                if color == CUSTOM
                else INTERIOR_COLORS[color].hex
                if color in INTERIOR_COLORS
                else None
            )
            payload = {"color": color, "hex": hex_value, "parts": tuple(raw.get("parts") or ())}
    try:
        model = PARAM_MODELS[operation].model_validate(payload)
    except ValidationError as exc:
        raise OperationParametersError(str(exc)) from exc
    return model.model_dump(mode="json")


def required_images(operation: Operation, params: dict[str, Any]) -> int:
    if operation is Operation.WHEELS:
        return 2
    if operation is Operation.BACKGROUND and params.get("background") == CUSTOM:
        return 2
    return 1


def describe_parameters(operation: Operation, params: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    match operation:
        case Operation.PLATE:
            lines.append("Табличка: фирменная EcoDrive Auto")
        case Operation.BACKGROUND:
            bg = params["background"]
            title = "🖼 Свой референс" if bg == CUSTOM else BACKGROUND_PRESETS[bg].title
            lines.append(f"Фон: {title}")
        case Operation.WHEELS:
            lines.append(f"Размер дисков: {WHEEL_SIZES[params['size_mode']][0]}")
        case Operation.INTERIOR_COLOR:
            color = params["color"]
            name = "Пользовательский" if color == CUSTOM else INTERIOR_COLORS[color].title
            lines.append(f"Цвет: {name} ({params['hex']})")
            parts = ", ".join(INTERIOR_PARTS[p][0] for p in params["parts"])
            lines.append(f"Элементы: {parts}")
    return lines


def format_eta(operation: Operation, queue_ahead: int = 0) -> str:
    low, high = ETA_SECONDS[operation]
    low += queue_ahead * low
    high += queue_ahead * high

    def fmt(seconds: int) -> str:
        return f"{seconds} сек" if seconds < 90 else f"{round(seconds / 60)} мин"

    return f"≈ {fmt(low)} – {fmt(high)}"


def build_summary(
    operation: Operation, params: dict[str, Any], *, images: int, queue_ahead: int = 0
) -> str:
    lines = [
        "<b>Проверьте задание</b>",
        "",
        f"Операция: {OPERATION_TITLES[operation]}",
        f"Изображений: {images}",
        *describe_parameters(operation, params),
        f"Ориентировочное время: {format_eta(operation, queue_ahead)}",
    ]
    return "\n".join(lines)
