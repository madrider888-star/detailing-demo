"""Состояния FSM и декларативное описание пошаговых сценариев.

Каждый сценарий — последовательность шагов. Обработчики в боте общие для всех
сценариев: они спрашивают у `Flow`, какой шаг следующий / предыдущий, поэтому
логику переходов легко тестировать без Telegram.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from aiogram.fsm.state import State, StatesGroup

from app.core.enums import Operation
from app.services.operations import (
    BACKGROUND_PRESETS,
    CUSTOM,
    INTERIOR_COLORS,
    INTERIOR_PARTS,
    WHEEL_SIZES,
)


class PlateStates(StatesGroup):
    photo = State()
    summary = State()


class BackgroundStates(StatesGroup):
    photo = State()
    background = State()
    reference = State()
    summary = State()


class WheelStates(StatesGroup):
    photo = State()
    reference = State()
    size = State()
    summary = State()


class InteriorStates(StatesGroup):
    photo = State()
    color = State()
    hex = State()
    parts = State()
    summary = State()


class ReportStates(StatesGroup):
    comment = State()


class StepKind(StrEnum):
    PHOTO = "photo"
    CHOICE = "choice"
    MULTI = "multi"
    HEX = "hex"
    SUMMARY = "summary"


@dataclass(frozen=True)
class Step:
    name: str
    kind: StepKind
    prompt: str
    key: str | None = None
    options: tuple[tuple[str, str], ...] = ()
    when: Callable[[dict[str, Any]], bool] | None = None

    def is_active(self, data: dict[str, Any]) -> bool:
        return self.when is None or self.when(data)

    def is_filled(self, data: dict[str, Any]) -> bool:
        if self.kind is StepKind.SUMMARY or self.key is None:
            return True
        return bool(data.get(self.key))


@dataclass(frozen=True)
class Flow:
    operation: Operation
    states: type[StatesGroup]
    steps: tuple[Step, ...]

    def state_for(self, step: Step) -> State:
        state = getattr(self.states, step.name)
        assert isinstance(state, State)
        return state

    def step(self, name: str) -> Step:
        for step in self.steps:
            if step.name == name:
                return step
        raise KeyError(name)

    def active_steps(self, data: dict[str, Any]) -> list[Step]:
        return [s for s in self.steps if s.is_active(data)]

    def first_step(self) -> Step:
        return self.steps[0]

    def next_step(self, current: str, data: dict[str, Any]) -> Step | None:
        active = self.active_steps(data)
        names = [s.name for s in active]
        if current not in names:
            return active[0]
        idx = names.index(current)
        return active[idx + 1] if idx + 1 < len(active) else None

    def prev_step(self, current: str, data: dict[str, Any]) -> Step | None:
        active = self.active_steps(data)
        names = [s.name for s in active]
        if current not in names:
            return None
        idx = names.index(current)
        return active[idx - 1] if idx > 0 else None

    def position(self, current: str, data: dict[str, Any]) -> tuple[int, int]:
        names = [s.name for s in self.active_steps(data)]
        return (names.index(current) + 1 if current in names else 1), len(names)

    def effective_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Данные только активных шагов (например, без референса, если выбран пресет)."""
        result = dict(data)
        for step in self.steps:
            if step.key and not step.is_active(data):
                result.pop(step.key, None)
        return result

    def image_keys(self, data: dict[str, Any]) -> list[str]:
        return [
            s.key
            for s in self.active_steps(data)
            if s.kind is StepKind.PHOTO and s.key and data.get(s.key)
        ]


PHOTO_HINT = (
    "Для максимального качества отправьте фото <b>файлом</b> (📎 → Файл), а не сжатой фотографией."
)

SUMMARY_STEP = Step("summary", StepKind.SUMMARY, "Проверьте параметры и нажмите «Подтвердить».")

FLOWS: dict[Operation, Flow] = {
    Operation.PLATE: Flow(
        Operation.PLATE,
        PlateStates,
        (
            Step(
                "photo",
                StepKind.PHOTO,
                "📷 Отправьте фотографию автомобиля, на которой виден передний или задний "
                "номер.\n\n" + PHOTO_HINT,
                key="original",
            ),
            SUMMARY_STEP,
        ),
    ),
    Operation.BACKGROUND: Flow(
        Operation.BACKGROUND,
        BackgroundStates,
        (
            Step(
                "photo",
                StepKind.PHOTO,
                "📷 Отправьте фотографию автомобиля.\n\n" + PHOTO_HINT,
                key="original",
            ),
            Step(
                "background",
                StepKind.CHOICE,
                "🏙 Выберите новый фон или пришлите свой референс.",
                key="background",
                options=(
                    *((k, v.title) for k, v in BACKGROUND_PRESETS.items()),
                    (CUSTOM, "🖼 Свой референс"),
                ),
            ),
            Step(
                "reference",
                StepKind.PHOTO,
                "🖼 Отправьте фотографию фона-референса (без автомобилей и людей в кадре).",
                key="reference",
                when=lambda d: d.get("background") == CUSTOM,
            ),
            SUMMARY_STEP,
        ),
    ),
    Operation.WHEELS: Flow(
        Operation.WHEELS,
        WheelStates,
        (
            Step(
                "photo",
                StepKind.PHOTO,
                "📷 Отправьте фотографию автомобиля, на которой хорошо видны колёса.\n\n"
                + PHOTO_HINT,
                key="original",
            ),
            Step(
                "reference",
                StepKind.PHOTO,
                "🛞 Отправьте фотографию диска-референса: диск анфас, крупно, при хорошем "
                "освещении.",
                key="reference",
            ),
            Step(
                "size",
                StepKind.CHOICE,
                "📏 Размер дисков:",
                key="size_mode",
                options=tuple((k, v[0]) for k, v in WHEEL_SIZES.items()),
            ),
            SUMMARY_STEP,
        ),
    ),
    Operation.INTERIOR_COLOR: Flow(
        Operation.INTERIOR_COLOR,
        InteriorStates,
        (
            Step(
                "photo",
                StepKind.PHOTO,
                "📷 Отправьте фотографию салона.\n\n" + PHOTO_HINT,
                key="original",
            ),
            Step(
                "color",
                StepKind.CHOICE,
                "🎨 Выберите цвет:",
                key="color",
                options=(
                    *((k, v.title) for k, v in INTERIOR_COLORS.items()),
                    (CUSTOM, "#️⃣ Свой HEX"),
                ),
            ),
            Step(
                "hex",
                StepKind.HEX,
                "#️⃣ Отправьте HEX-код цвета, например <code>#8B4513</code>.",
                key="hex",
                when=lambda d: d.get("color") == CUSTOM,
            ),
            Step(
                "parts",
                StepKind.MULTI,
                "🧩 Выберите элементы для изменения (можно несколько), затем «Подтвердить».",
                key="parts",
                options=tuple((k, v[0]) for k, v in INTERIOR_PARTS.items()),
            ),
            SUMMARY_STEP,
        ),
    ),
}

FLOW_BY_GROUP: dict[str, Flow] = {flow.states.__full_group_name__: flow for flow in FLOWS.values()}


def flow_for_state(state: str | None) -> tuple[Flow, Step] | None:
    """По строке состояния FSM ("WheelStates:size") находит сценарий и шаг."""
    if not state or ":" not in state:
        return None
    group, name = state.split(":", 1)
    flow = FLOW_BY_GROUP.get(group)
    if flow is None:
        return None
    try:
        return flow, flow.step(name)
    except KeyError:
        return None
