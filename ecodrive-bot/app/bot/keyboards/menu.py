from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.callbacks import MenuCb

MAIN_MENU_ITEMS: tuple[tuple[str, str], ...] = (
    ("plate", "🔢 Заменить номерную табличку"),
    ("background", "🏙 Заменить фон"),
    ("wheels", "🛞 Заменить колёсные диски"),
    ("interior_color", "🎨 Изменить цвет салона"),
    ("my_jobs", "📂 Мои обработки"),
    ("help", "ℹ️ Инструкция"),
)


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for action, title in MAIN_MENU_ITEMS:
        builder.button(text=title, callback_data=MenuCb(action=action))
    builder.adjust(1)
    return builder.as_markup()


def home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню", callback_data=MenuCb(action="home").pack()
                )
            ]
        ]
    )
