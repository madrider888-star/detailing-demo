from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.callbacks import NavCb, OptCb
from app.bot.states.flows import Step, StepKind


def nav_rows() -> list[list[InlineKeyboardButton]]:
    def btn(text: str, action: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=NavCb(action=action).pack())

    return [
        [btn("✅ Подтвердить", "confirm"), btn("🔄 Переделать", "redo")],
        [btn("⬅️ Назад", "back"), btn("✖️ Отмена", "cancel")],
    ]


def step_kb(step: Step, data: dict[str, Any]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if step.kind in (StepKind.CHOICE, StepKind.MULTI) and step.key:
        current = data.get(step.key)
        selected = set(current or []) if step.kind is StepKind.MULTI else {current}
        for value, title in step.options:
            mark = "✅ " if value in selected else ""
            builder.button(text=f"{mark}{title}", callback_data=OptCb(value=value))
        builder.adjust(2 if len(step.options) > 4 else 1)
    for row in nav_rows():
        builder.row(*row)
    return builder.as_markup()
