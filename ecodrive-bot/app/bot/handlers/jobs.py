"""Кнопки после обработки: оригинал, результат, переделать, жалоба, оператор."""

from __future__ import annotations

import html

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.context import AppContext
from app.bot.handlers.flow import enqueue_and_announce, start_flow, to_main_menu
from app.bot.keyboards.callbacks import JobCb, ReportCb
from app.bot.keyboards.jobs import admin_jobs_kb, report_kb, result_kb
from app.bot.staff import notify_staff
from app.bot.states.flows import ReportStates
from app.core.enums import OPERATION_TITLES, AssetType, Operation
from app.core.errors import AppError
from app.models import Job, User
from app.repositories.assets import AssetRepository
from app.services.jobs import JobService

router = Router(name="jobs")


def _service(session: AsyncSession, ctx: AppContext) -> JobService:
    return JobService(session, ctx.storage, ctx.settings, ctx.provider_name)


async def _send_asset(
    callback: CallbackQuery,
    job: Job,
    asset_type: AssetType,
    ctx: AppContext,
    session: AsyncSession,
) -> None:
    asset = await AssetRepository(session).latest(job.id, asset_type)
    if asset is None or not isinstance(callback.message, Message):
        await callback.answer("Файл не найден", show_alert=True)
        return
    await callback.answer("Отправляю файл…")
    data = await ctx.storage.get(asset.storage_key)
    ext = asset.storage_key.rsplit(".", 1)[-1]
    if asset_type is AssetType.ORIGINAL:
        name, caption, markup = f"original_{job.id:04d}.{ext}", f"📥 Оригинал {job.number}", None
    else:
        name = f"ecodrive_{job.id:04d}_{job.operation.value}.{ext}"
        caption, markup = f"✅ Результат {job.number}", result_kb(job.id)
    await callback.message.answer_document(
        BufferedInputFile(data, filename=name),
        caption=caption,
        reply_markup=markup,
        disable_content_type_detection=True,
    )


@router.callback_query(JobCb.filter(F.action.in_({"original", "result"})))
async def on_download(
    callback: CallbackQuery,
    callback_data: JobCb,
    ctx: AppContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    try:
        job = await _service(session, ctx).get_owned(db_user, callback_data.job_id)
    except AppError as exc:
        await callback.answer(exc.user_message, show_alert=True)
        return
    asset_type = AssetType.ORIGINAL if callback_data.action == "original" else AssetType.RESULT
    await _send_asset(callback, job, asset_type, ctx, session)


@router.callback_query(JobCb.filter(F.action == "redo"))
async def on_redo_job(
    callback: CallbackQuery,
    callback_data: JobCb,
    ctx: AppContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    try:
        job = await _service(session, ctx).redo(
            db_user, callback_data.job_id, callback.message.chat.id
        )
        await session.commit()
    except AppError as exc:
        await session.rollback()
        await callback.answer(exc.user_message, show_alert=True)
        return
    await callback.answer(f"Создано задание {job.number}")
    await enqueue_and_announce(callback.message, job, ctx, session)


@router.callback_query(JobCb.filter(F.action == "other_photo"))
async def on_other_photo(callback: CallbackQuery, state: FSMContext, ctx: AppContext) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(reply_markup=None)
    await start_flow(callback, state, Operation.PLATE, ctx)


@router.callback_query(JobCb.filter(F.action == "manual"))
async def on_manual(callback: CallbackQuery) -> None:
    await callback.answer(texts.MANUAL_SOON, show_alert=True)


@router.callback_query(JobCb.filter(F.action == "operator"))
async def on_operator(
    callback: CallbackQuery,
    callback_data: JobCb,
    ctx: AppContext,
    session: AsyncSession,
    db_user: User,
    bot: Bot,
) -> None:
    try:
        job = await _service(session, ctx).handoff_to_operator(db_user, callback_data.job_id)
    except AppError as exc:
        await callback.answer(exc.user_message, show_alert=True)
        return
    original = await AssetRepository(session).latest(job.id, AssetType.ORIGINAL)
    document = None
    if original is not None:
        ext = original.storage_key.rsplit(".", 1)[-1]
        document = (await ctx.storage.get(original.storage_key), f"original_{job.id:04d}.{ext}")
    text = (
        f"👤 Нужна ручная обработка {job.number}\n"
        f"{OPERATION_TITLES[job.operation]}\n"
        f"Сотрудник: {html.escape(db_user.display_name)} (<code>{db_user.telegram_id}</code>)"
    )
    await notify_staff(
        bot, session, ctx.settings, text, document=document, markup=admin_jobs_kb([job])
    )
    await callback.answer("Передано оператору. С вами свяжутся.", show_alert=True)


# ─────────────────────────── сообщить о проблеме ───────────────────────────


@router.callback_query(JobCb.filter(F.action == "report"))
async def on_report(callback: CallbackQuery, callback_data: JobCb, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ReportStates.comment)
    await state.set_data({"report_job_id": callback_data.job_id})
    if isinstance(callback.message, Message):
        await callback.message.answer(
            f"⚠️ Опишите проблему с заданием #{callback_data.job_id:04d} одним сообщением "
            "(что не так на результате).",
            reply_markup=report_kb(),
        )


async def _finish_report(
    target: Message | CallbackQuery,
    state: FSMContext,
    comment: str | None,
    ctx: AppContext,
    session: AsyncSession,
    user: User,
    bot: Bot,
) -> None:
    data = await state.get_data()
    job_id = data.get("report_job_id")
    if not isinstance(job_id, int):
        await to_main_menu(target, state)
        return
    try:
        job = await _service(session, ctx).report_problem(user, job_id, comment)
    except AppError as exc:
        await to_main_menu(target, state, exc.user_message)
        return
    text = (
        f"⚠️ Жалоба на результат {job.number}\n"
        f"{OPERATION_TITLES[job.operation]}\n"
        f"Сотрудник: {html.escape(user.display_name)}\n"
        f"Комментарий: {html.escape(comment or '—')}"
    )
    await notify_staff(bot, session, ctx.settings, text, markup=admin_jobs_kb([job]))
    await to_main_menu(target, state, "Спасибо! Передали модератору.")


@router.message(ReportStates.comment, F.text)
async def on_report_text(
    message: Message,
    state: FSMContext,
    ctx: AppContext,
    session: AsyncSession,
    db_user: User,
    bot: Bot,
) -> None:
    await _finish_report(message, state, (message.text or "")[:1000], ctx, session, db_user, bot)


@router.callback_query(ReportStates.comment, ReportCb.filter(F.action == "skip"))
async def on_report_skip(
    callback: CallbackQuery,
    state: FSMContext,
    ctx: AppContext,
    session: AsyncSession,
    db_user: User,
    bot: Bot,
) -> None:
    await callback.answer()
    await _finish_report(callback, state, None, ctx, session, db_user, bot)


@router.callback_query(ReportCb.filter(F.action == "cancel"))
async def on_report_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(texts.CANCELLED)
    await to_main_menu(callback, state, texts.CANCELLED)
