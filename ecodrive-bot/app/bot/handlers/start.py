"""/start, главное меню, инструкция, «Мои обработки»."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.handlers.flow import to_main_menu
from app.bot.keyboards.callbacks import MenuCb
from app.bot.keyboards.jobs import my_jobs_kb
from app.bot.keyboards.menu import home_kb, main_menu_kb
from app.bot.telegram_io import show
from app.models import User
from app.repositories.jobs import JobRepository

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.WELCOME, reply_markup=main_menu_kb())


@router.message(Command("menu", "cancel"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await to_main_menu(message, state)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP, reply_markup=home_kb())


@router.callback_query(MenuCb.filter(F.action == "home"))
async def on_home(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    # Под документом с результатом нельзя заменить текст — отправляем меню новым сообщением.
    if callback.message is not None and getattr(callback.message, "document", None):
        await callback.message.answer(texts.MAIN_MENU, reply_markup=main_menu_kb())
        return
    await show(callback, texts.MAIN_MENU, main_menu_kb())


@router.callback_query(MenuCb.filter(F.action == "help"))
async def on_help(callback: CallbackQuery) -> None:
    await callback.answer()
    await show(callback, texts.HELP, home_kb())


async def _my_jobs(session: AsyncSession, user: User) -> tuple[str, InlineKeyboardMarkup]:
    jobs = list(await JobRepository(session).list_for_user(user.id, limit=10))
    if not jobs:
        return "📂 У вас пока нет обработок.", home_kb()
    lines = ["📂 <b>Последние обработки</b>", "", *(texts.job_line(job) for job in jobs)]
    return "\n".join(lines), my_jobs_kb(jobs)


@router.callback_query(MenuCb.filter(F.action == "my_jobs"))
async def on_my_jobs(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await callback.answer()
    text, markup = await _my_jobs(session, db_user)
    await show(callback, text, markup)


@router.message(Command("my"))
async def cmd_my_jobs(message: Message, session: AsyncSession, db_user: User) -> None:
    text, markup = await _my_jobs(session, db_user)
    await message.answer(text, reply_markup=markup)
