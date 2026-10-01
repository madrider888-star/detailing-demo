"""Общий обработчик пошаговых сценариев (все четыре операции)."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.context import AppContext
from app.bot.keyboards.callbacks import MenuCb, NavCb, OptCb
from app.bot.keyboards.flow import step_kb
from app.bot.keyboards.menu import main_menu_kb
from app.bot.states.flows import FLOWS, Flow, Step, StepKind, flow_for_state
from app.bot.telegram_io import IncomingFile, download_file, extract_incoming_file, show
from app.core.enums import OPERATION_TITLES, AssetType, JobStatus, Operation
from app.core.errors import AppError, ImageValidationError
from app.core.logging import get_logger
from app.models import Job, User
from app.repositories.jobs import JobRepository
from app.services.image_validation import ValidatedImage, validate_image
from app.services.jobs import JobImage, JobService
from app.services.operations import (
    OperationParametersError,
    build_parameters,
    build_summary,
    normalize_hex,
)
from app.services.reference_check import assess_wheel_reference

log = get_logger(__name__)
router = Router(name="flow")

FLOW_OPERATIONS = {op.value for op in FLOWS}


class InFlow(BaseFilter):
    """Совпадает, если пользователь внутри сценария; передаёт `flow` и `step`."""

    async def __call__(self, event: Any, state: FSMContext) -> bool | dict[str, Any]:
        found = flow_for_state(await state.get_state())
        if found is None:
            return False
        flow, step = found
        return {"flow": flow, "step": step}


# ─────────────────────────── отрисовка ───────────────────────────


async def render_step(
    flow: Flow, step: Step, data: dict[str, Any], ctx: AppContext
) -> tuple[str, InlineKeyboardMarkup]:
    pos, total = flow.position(step.name, data)
    header = f"<b>{OPERATION_TITLES[flow.operation]}</b> · шаг {pos} из {total}\n\n"
    body = step.prompt
    if step.kind is StepKind.PHOTO and step.key and data.get(step.key):
        meta = data[step.key]
        body += f"\n\n✅ Получено: {meta['w']}×{meta['h']}"
        if meta.get("compressed"):
            body += "\n" + texts.COMPRESSED_PHOTO_NOTE
        for warning in meta.get("warnings", []):
            body += f"\n⚠️ Референс: {warning}"
        body += "\n\nНажмите «Подтвердить», чтобы продолжить, или «Переделать»."
    elif step.kind is StepKind.HEX and data.get("hex"):
        body += f"\n\nТекущий цвет: <code>{data['hex']}</code>"
    elif step.kind is StepKind.SUMMARY:
        effective = flow.effective_data(data)
        try:
            params = build_parameters(flow.operation, effective)
        except OperationParametersError:
            body = "⚠️ Не все параметры заполнены. Нажмите «Назад» и проверьте шаги."
        else:
            try:
                queue_ahead = await ctx.queue.size()
            except Exception:  # очередь недоступна — оценка без учёта очереди
                queue_ahead = 0
            body = build_summary(
                flow.operation,
                params,
                images=len(flow.image_keys(effective)),
                queue_ahead=queue_ahead,
            )
    return header + body, step_kb(step, data)


async def go_to(
    target: Message | CallbackQuery,
    state: FSMContext,
    flow: Flow,
    step: Step,
    ctx: AppContext,
) -> None:
    await state.set_state(flow.state_for(step))
    data = await state.get_data()
    text, markup = await render_step(flow, step, data, ctx)
    await show(target, text, markup)


async def start_flow(
    target: Message | CallbackQuery, state: FSMContext, operation: Operation, ctx: AppContext
) -> None:
    flow = FLOWS[operation]
    await state.clear()
    await state.set_data({"flow": operation.value, "nonce": uuid.uuid4().hex})
    await go_to(target, state, flow, flow.first_step(), ctx)


async def to_main_menu(
    target: Message | CallbackQuery, state: FSMContext, prefix: str = ""
) -> None:
    await state.clear()
    text = f"{prefix}\n\n{texts.MAIN_MENU}" if prefix else texts.MAIN_MENU
    await show(target, text, main_menu_kb())


# ─────────────────────────── вход в сценарий ───────────────────────────


@router.callback_query(MenuCb.filter(F.action.in_(FLOW_OPERATIONS)))
async def on_operation_selected(
    callback: CallbackQuery, callback_data: MenuCb, state: FSMContext, ctx: AppContext
) -> None:
    await callback.answer()
    await start_flow(callback, state, Operation(callback_data.action), ctx)


# ─────────────────────────── навигация ───────────────────────────


@router.callback_query(NavCb.filter(F.action == "cancel"))
async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(texts.CANCELLED)
    await to_main_menu(callback, state, texts.CANCELLED)


@router.callback_query(NavCb.filter(), ~InFlow())
async def on_nav_without_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(texts.NO_ACTIVE_FLOW, show_alert=True)
    await to_main_menu(callback, state)


@router.callback_query(NavCb.filter(F.action == "back"), InFlow())
async def on_back(
    callback: CallbackQuery, state: FSMContext, flow: Flow, step: Step, ctx: AppContext
) -> None:
    await callback.answer()
    prev = flow.prev_step(step.name, await state.get_data())
    if prev is None:
        await to_main_menu(callback, state)
        return
    await go_to(callback, state, flow, prev, ctx)


@router.callback_query(NavCb.filter(F.action == "redo"), InFlow())
async def on_redo(
    callback: CallbackQuery, state: FSMContext, flow: Flow, step: Step, ctx: AppContext
) -> None:
    await callback.answer("Повторим шаг")
    if step.kind is StepKind.SUMMARY:
        await start_flow(callback, state, flow.operation, ctx)
        return
    data = await state.get_data()
    if step.key:
        data.pop(step.key, None)
        await state.set_data(data)
    await go_to(callback, state, flow, step, ctx)


@router.callback_query(NavCb.filter(F.action == "confirm"), InFlow())
async def on_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    flow: Flow,
    step: Step,
    ctx: AppContext,
    session: AsyncSession,
    db_user: User,
    bot: Bot,
) -> None:
    data = await state.get_data()
    if step.kind is StepKind.SUMMARY:
        await submit_job(callback, state, flow, data, ctx, session, db_user, bot)
        return
    if not step.is_filled(data):
        hint = {
            StepKind.PHOTO: texts.NEED_PHOTO_FIRST,
            StepKind.CHOICE: texts.NEED_CHOICE_FIRST,
            StepKind.MULTI: texts.NEED_PARTS_FIRST,
            StepKind.HEX: texts.NEED_HEX_FIRST,
        }.get(step.kind, texts.NEED_CHOICE_FIRST)
        await callback.answer(hint, show_alert=True)
        return
    await callback.answer()
    nxt = flow.next_step(step.name, data)
    if nxt is not None:
        await go_to(callback, state, flow, nxt, ctx)


@router.callback_query(OptCb.filter(), InFlow())
async def on_option(
    callback: CallbackQuery,
    callback_data: OptCb,
    state: FSMContext,
    flow: Flow,
    step: Step,
    ctx: AppContext,
) -> None:
    allowed = {value for value, _ in step.options}
    if step.key is None or callback_data.value not in allowed:
        await callback.answer("Этот вариант сейчас недоступен", show_alert=True)
        return
    await callback.answer()
    data = await state.get_data()
    if step.kind is StepKind.MULTI:
        selected: list[str] = list(data.get(step.key) or [])
        if callback_data.value in selected:
            selected.remove(callback_data.value)
        else:
            selected.append(callback_data.value)
        data[step.key] = selected
        await state.set_data(data)
        await go_to(callback, state, flow, step, ctx)
        return
    data[step.key] = callback_data.value
    await state.set_data(data)
    nxt = flow.next_step(step.name, data)
    if nxt is not None:
        await go_to(callback, state, flow, nxt, ctx)


@router.callback_query(OptCb.filter())
async def on_option_without_flow(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer(texts.NO_ACTIVE_FLOW, show_alert=True)


# ─────────────────────────── входящие файлы и текст ───────────────────────────


@router.message(F.photo | F.document, InFlow())
async def on_media(
    message: Message, state: FSMContext, flow: Flow, step: Step, ctx: AppContext, bot: Bot
) -> None:
    if step.kind is not StepKind.PHOTO or step.key is None:
        await message.answer(texts.PHOTO_NOT_EXPECTED)
        return
    incoming = extract_incoming_file(message)
    if incoming is None:
        return
    s = ctx.settings
    try:
        raw = await download_file(bot, incoming, s.max_upload_bytes)
        # Декодирование большого фото — CPU-работа: не блокируем event loop бота.
        image = await asyncio.to_thread(
            validate_image,
            raw,
            declared_mime=incoming.declared_mime,
            max_bytes=s.max_upload_bytes,
            max_pixels=s.max_image_pixels,
            min_side=s.min_image_side,
        )
    except ImageValidationError as exc:
        log.info("upload.rejected", reason=str(exc))
        await message.answer(f"⚠️ {exc.user_message}")
        return

    meta: dict[str, Any] = {
        "file_id": incoming.file_id,
        "mime": image.mime_type,
        "w": image.width,
        "h": image.height,
        "compressed": incoming.compressed,
    }
    if flow.operation is Operation.WHEELS and step.key == "reference":
        meta["warnings"] = await asyncio.to_thread(assess_wheel_reference, image.data)
    data = await state.get_data()
    data[step.key] = meta
    await state.set_data(data)
    await go_to(message, state, flow, step, ctx)


@router.message(F.text, InFlow())
async def on_text(
    message: Message, state: FSMContext, flow: Flow, step: Step, ctx: AppContext
) -> None:
    if step.kind is not StepKind.HEX:
        await message.answer(texts.TEXT_NOT_EXPECTED)
        return
    value = normalize_hex(message.text or "")
    if value is None:
        await message.answer(texts.INVALID_HEX)
        return
    data = await state.get_data()
    data["hex"] = value
    await state.set_data(data)
    nxt = flow.next_step(step.name, data)
    if nxt is not None:
        await go_to(message, state, flow, nxt, ctx)


# ─────────────────────────── создание задания ───────────────────────────


async def _load_images(
    bot: Bot, flow: Flow, data: dict[str, Any], ctx: AppContext
) -> list[JobImage]:
    s = ctx.settings
    images: list[JobImage] = []
    for key in flow.image_keys(data):
        meta = data[key]
        incoming = IncomingFile(
            meta["file_id"], None, meta.get("mime"), bool(meta.get("compressed"))
        )
        raw = await download_file(bot, incoming, s.max_upload_bytes)
        validated: ValidatedImage = await asyncio.to_thread(
            validate_image,
            raw,
            declared_mime=meta.get("mime"),
            max_bytes=s.max_upload_bytes,
            max_pixels=s.max_image_pixels,
            min_side=s.min_image_side,
        )
        asset_type = AssetType.ORIGINAL if key == "original" else AssetType.REFERENCE
        images.append(JobImage(asset_type, validated))
    return images


async def enqueue_and_announce(
    message: Message, job: Job, ctx: AppContext, session: AsyncSession
) -> None:
    """Статус-сообщение → сохранить его id → поставить в очередь."""
    repo = JobRepository(session)
    status_message = await message.answer(texts.job_status_text(job))
    await repo.set_status_message(job.id, status_message.chat.id, status_message.message_id)
    await session.commit()
    try:
        await ctx.queue.enqueue(job.id, job.attempts)
    except Exception:
        log.exception("queue.enqueue_failed", job_id=job.id)
        await repo.transition(
            job.id,
            from_statuses=[JobStatus.QUEUED],
            to=JobStatus.FAILED,
            error_message="queue unavailable",
        )
        await session.commit()
        await status_message.edit_text(
            texts.job_status_text(
                job,
                "❌ Очередь обработки недоступна. Попробуйте позже или сообщите администратору.",
            )
        )


async def submit_job(
    callback: CallbackQuery,
    state: FSMContext,
    flow: Flow,
    data: dict[str, Any],
    ctx: AppContext,
    session: AsyncSession,
    user: User,
    bot: Bot,
) -> None:
    message = callback.message
    if not isinstance(message, Message):
        await callback.answer()
        return
    effective = flow.effective_data(data)
    try:
        images = await _load_images(bot, flow, effective, ctx)
        job = await JobService(session, ctx.storage, ctx.settings, ctx.provider_name).create_job(
            user=user,
            operation=flow.operation,
            raw_params=effective,
            images=images,
            idempotency_key=data.get("nonce"),
            chat_id=message.chat.id,
        )
        await session.commit()
    except AppError as exc:
        await session.rollback()
        await callback.answer(exc.user_message, show_alert=True)
        return
    except (OperationParametersError, ValueError) as exc:
        await session.rollback()
        log.warning("job.params_invalid", error=str(exc))
        await callback.answer("Не все шаги заполнены. Проверьте параметры.", show_alert=True)
        return

    await callback.answer("Задание создано")
    await state.clear()
    try:
        await message.edit_text(f"✅ Задание <b>{job.number}</b> создано.", reply_markup=None)
    except Exception:  # сообщение могло быть удалено — не критично
        log.debug("summary.edit_failed", job_id=job.id)
    await enqueue_and_announce(message, job, ctx, session)
