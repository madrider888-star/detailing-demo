"""Администрирование через команды Telegram."""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.context import AppContext
from app.bot.filters import RoleFilter
from app.bot.keyboards.callbacks import AdminCb
from app.bot.keyboards.jobs import admin_jobs_kb
from app.core.enums import OPERATION_TITLES, STATUS_TITLES, JobStatus, Operation, Role
from app.core.errors import AppError
from app.models import User
from app.repositories.jobs import JobRepository
from app.repositories.users import UserRepository
from app.services.access import AccessService
from app.services.jobs import JobService

router = Router(name="admin")
staff = RoleFilter(Role.MODERATOR)
admins_only = RoleFilter(Role.ADMIN)

ADMIN_HELP = (
    "🛠 <b>Администрирование</b>\n\n"
    "/stats — статистика и очередь\n"
    "/jobs — последние задания\n"
    "/failed — ошибки и задания на проверке\n"
    "/users — пользователи (admin)\n"
    "/allow_user &lt;telegram_id&gt; [employee|moderator|admin] — дать доступ (admin)\n"
    "/block_user &lt;telegram_id&gt; — заблокировать (admin)"
)


@router.message(Command("admin"), staff)
async def cmd_admin(message: Message) -> None:
    await message.answer(ADMIN_HELP)


@router.message(Command("stats"), staff)
async def cmd_stats(message: Message, session: AsyncSession, ctx: AppContext) -> None:
    repo = JobRepository(session)
    by_op = await repo.counts_by_operation()
    by_status = await repo.counts_by_status()
    try:
        queue_size: int | str = await ctx.queue.size()
    except Exception:
        queue_size = "недоступна"
    total = sum(by_status.values())
    lines = [f"📊 <b>Статистика</b>\n\nВсего обработок: <b>{total}</b>", "", "<b>По операциям</b>"]
    for op in Operation:
        lines.append(f"{OPERATION_TITLES[op]}: {by_op.get(op.value, 0)}")
    lines += ["", "<b>По статусам</b>"]
    for status in JobStatus:
        lines.append(f"{STATUS_TITLES[status]}: {by_status.get(status.value, 0)}")
    active = by_status.get("queued", 0) + by_status.get("processing", 0)
    lines += ["", f"Текущая очередь (ARQ): {queue_size}", f"Активных заданий в БД: {active}"]
    await message.answer("\n".join(lines))


@router.message(Command("jobs"), staff)
async def cmd_jobs(message: Message, session: AsyncSession) -> None:
    jobs = await JobRepository(session).list_recent(limit=15)
    if not jobs:
        await message.answer("Заданий пока нет.")
        return
    text = "🗂 <b>Последние задания</b>\n\n" + "\n".join(texts.job_line(j, True) for j in jobs)
    await message.answer(text, reply_markup=admin_jobs_kb(jobs))


@router.message(Command("failed"), staff)
async def cmd_failed(message: Message, session: AsyncSession) -> None:
    jobs = await JobRepository(session).list_recent(
        limit=15, statuses=[JobStatus.FAILED, JobStatus.NEEDS_REVIEW]
    )
    if not jobs:
        await message.answer("✅ Ошибок нет.")
        return
    lines = ["❌ <b>Ошибки и задания на проверке</b>", ""]
    for job in jobs:
        lines.append(texts.job_line(job, True))
        if job.status is JobStatus.NEEDS_REVIEW and job.error_message:
            lines.append(f"   ↳ <i>{html.escape(job.error_message[:160])}</i>")
    await message.answer("\n".join(lines), reply_markup=admin_jobs_kb(jobs))


@router.callback_query(AdminCb.filter(F.action == "retry"), staff)
async def on_retry(
    callback: CallbackQuery,
    callback_data: AdminCb,
    session: AsyncSession,
    db_user: User,
    ctx: AppContext,
) -> None:
    service = JobService(session, ctx.storage, ctx.settings, ctx.provider_name)
    try:
        job = await service.retry(db_user, callback_data.job_id)
        await session.commit()
    except AppError as exc:
        await session.rollback()
        await callback.answer(exc.user_message, show_alert=True)
        return
    await ctx.queue.enqueue(job.id, job.attempts)
    await callback.answer(f"Задание {job.number} поставлено в очередь повторно", show_alert=True)


@router.callback_query(AdminCb.filter())
async def on_admin_denied(callback: CallbackQuery) -> None:
    await callback.answer("Недостаточно прав", show_alert=True)


@router.message(Command("users"), admins_only)
async def cmd_users(message: Message, session: AsyncSession) -> None:
    users = await UserRepository(session).list_all()
    lines = ["👥 <b>Пользователи</b>", ""]
    for u in users:
        status = "✅" if u.is_active else "⛔"
        lines.append(
            f"{status} <code>{u.telegram_id}</code> {html.escape(u.display_name)} — {u.role.value}"
        )
    await message.answer("\n".join(lines))


def _parse_target(command: CommandObject) -> tuple[int, Role] | None:
    args = (command.args or "").split()
    if not args or not args[0].lstrip("-").isdigit():
        return None
    role = Role.EMPLOYEE
    if len(args) > 1:
        try:
            role = Role(args[1].lower())
        except ValueError:
            return None
    return int(args[0]), role


@router.message(Command("allow_user"), admins_only)
async def cmd_allow_user(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
    ctx: AppContext,
) -> None:
    parsed = _parse_target(command)
    if parsed is None:
        await message.answer(
            "Использование: <code>/allow_user 123456789 [employee|moderator|admin]</code>"
        )
        return
    telegram_id, role = parsed
    user = await AccessService(session, ctx.settings).allow_user(db_user, telegram_id, role)
    await message.answer(f"✅ Доступ выдан: <code>{user.telegram_id}</code>, роль {role.value}")


@router.message(Command("block_user"), admins_only)
async def cmd_block_user(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
    ctx: AppContext,
) -> None:
    parsed = _parse_target(command)
    if parsed is None:
        await message.answer("Использование: <code>/block_user 123456789</code>")
        return
    telegram_id, _ = parsed
    if telegram_id == db_user.telegram_id:
        await message.answer("Нельзя заблокировать самого себя.")
        return
    user = await AccessService(session, ctx.settings).block_user(db_user, telegram_id)
    if user is None:
        await message.answer("Этот ID указан в ADMIN_TELEGRAM_IDS — уберите его из .env.")
        return
    await message.answer(f"⛔ Пользователь <code>{telegram_id}</code> заблокирован.")


@router.message(Command("admin", "stats", "jobs", "failed", "users", "allow_user", "block_user"))
async def cmd_no_rights(message: Message) -> None:
    await message.answer("Недостаточно прав для этой команды.")
