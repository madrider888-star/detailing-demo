"""Сквозные тесты Telegram-интерфейса: реальные обработчики aiogram + FSM + БД."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import AnswerCallbackQuery, SendMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot.context import AppContext
from app.bot.dispatcher import create_dispatcher
from app.bot.states.flows import BackgroundStates, InteriorStates, PlateStates, WheelStates
from app.core.config import Settings
from app.core.enums import AssetType, JobStatus, Operation
from app.models import Asset, Job
from app.services.storage import LocalStorage
from app.workers.queue import InMemoryJobQueue
from tests.conftest import EMPLOYEE_ID, STRANGER_ID
from tests.fake_telegram import FakeSession, UpdateFactory, make_bot


@dataclass
class Harness:
    dp: Dispatcher
    bot: Bot
    session: FakeSession
    fsm: MemoryStorage
    queue: InMemoryJobQueue
    updates: UpdateFactory
    session_factory: async_sessionmaker[AsyncSession]

    async def feed(self, update: object) -> None:
        await self.dp.feed_update(self.bot, update)  # type: ignore[arg-type]

    async def state(self) -> str | None:
        key = StorageKey(bot_id=self.bot.id, chat_id=EMPLOYEE_ID, user_id=EMPLOYEE_ID)
        return await self.fsm.get_state(key)

    async def data(self) -> dict[str, object]:
        key = StorageKey(bot_id=self.bot.id, chat_id=EMPLOYEE_ID, user_id=EMPLOYEE_ID)
        return await self.fsm.get_data(key)

    def alerts(self) -> list[str]:
        return [r.text or "" for r in self.session.sent(AnswerCallbackQuery) if r.show_alert]


@pytest.fixture
async def harness(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalStorage,
) -> Harness:
    queue = InMemoryJobQueue()
    ctx = AppContext(
        settings=settings,
        session_factory=session_factory,
        storage=storage,
        queue=queue,
        provider_names=dict.fromkeys(Operation, "mock"),
    )
    fsm = MemoryStorage()
    dp = create_dispatcher(ctx, fsm)
    bot, fake = make_bot()
    return Harness(dp, bot, fake, fsm, queue, UpdateFactory(EMPLOYEE_ID), session_factory)


async def test_start_shows_catalog_menu(harness: Harness) -> None:
    await harness.feed(harness.updates.text("/start"))
    msg = harness.session.sent(SendMessage)[-1]
    buttons = [b.text for row in msg.reply_markup.inline_keyboard for b in row]
    assert buttons == [
        "🔢 Заменить номерную табличку",
        "🏙 Заменить фон",
        "🛞 Заменить колёсные диски",
        "🎨 Изменить цвет салона",
        "📂 Мои обработки",
        "ℹ️ Инструкция",
    ]


async def test_stranger_is_denied(harness: Harness) -> None:
    stranger = UpdateFactory(STRANGER_ID, "stranger")
    await harness.feed(stranger.text("/start"))
    assert "Доступ только для сотрудников" in harness.session.last_text()
    assert str(STRANGER_ID) in harness.session.last_text()


async def test_plate_flow_end_to_end(harness: Harness, car_jpeg: bytes) -> None:
    u = harness.updates
    await harness.feed(u.text("/start"))
    await harness.feed(u.callback("m:plate"))
    assert await harness.state() == PlateStates.photo.state

    # «Подтвердить» без фото — подсказка, состояние не меняется.
    await harness.feed(u.callback("nav:confirm"))
    assert "Сначала отправьте фото" in harness.alerts()
    assert await harness.state() == PlateStates.photo.state

    harness.session.files["car1"] = car_jpeg
    await harness.feed(u.document("car1", len(car_jpeg)))
    assert "Получено: 1280×860" in harness.session.last_text()
    await harness.feed(u.callback("nav:confirm"))
    assert await harness.state() == PlateStates.summary.state
    assert "Изображений: 1" in harness.session.last_text()

    await harness.feed(u.callback("nav:confirm"))
    assert await harness.state() is None
    assert harness.queue.items == [(1, 0)]
    assert any("Номер задания: <b>#0001</b>" in t for t in harness.session.texts())

    async with harness.session_factory() as s:
        job = (await s.execute(select(Job))).scalar_one()
        assets = (await s.execute(select(Asset))).scalars().all()
    assert job.status is JobStatus.QUEUED
    assert job.status_message_id is not None
    assert [a.asset_type for a in assets] == [AssetType.ORIGINAL]


async def test_double_confirm_creates_single_job(harness: Harness, car_jpeg: bytes) -> None:
    u = harness.updates
    await harness.feed(u.callback("m:plate"))
    harness.session.files["car1"] = car_jpeg
    await harness.feed(u.document("car1", len(car_jpeg)))
    await harness.feed(u.callback("nav:confirm"))
    data = await harness.data()
    await harness.feed(u.callback("nav:confirm"))
    # Повторное нажатие на старую сводку: восстанавливаем состояние и жмём снова.
    key = StorageKey(bot_id=harness.bot.id, chat_id=EMPLOYEE_ID, user_id=EMPLOYEE_ID)
    await harness.fsm.set_state(key, PlateStates.summary)
    await harness.fsm.set_data(key, data)
    await harness.feed(u.callback("nav:confirm"))
    async with harness.session_factory() as s:
        jobs = (await s.execute(select(Job))).scalars().all()
    assert len(jobs) == 1
    assert any("уже создано" in a for a in harness.alerts())


async def test_back_redo_cancel(harness: Harness, car_jpeg: bytes) -> None:
    u = harness.updates
    await harness.feed(u.callback("m:background"))
    harness.session.files["car1"] = car_jpeg
    await harness.feed(u.document("car1", len(car_jpeg)))
    await harness.feed(u.callback("nav:confirm"))
    assert await harness.state() == BackgroundStates.background.state

    await harness.feed(u.callback("nav:back"))
    assert await harness.state() == BackgroundStates.photo.state
    await harness.feed(u.callback("nav:redo"))
    assert "original" not in await harness.data()

    await harness.feed(u.document("car1", len(car_jpeg)))
    await harness.feed(u.callback("nav:confirm"))
    # Выбор пресета сразу ведёт к сводке, шаг референса пропускается.
    await harness.feed(u.callback("opt:dark_studio"))
    assert await harness.state() == BackgroundStates.summary.state
    assert "Тёмная премиальная студия" in harness.session.last_text()

    await harness.feed(u.callback("nav:cancel"))
    assert await harness.state() is None
    assert "Отменено" in harness.session.last_text()


async def test_background_custom_reference_requires_photo(
    harness: Harness, car_jpeg: bytes
) -> None:
    u = harness.updates
    await harness.feed(u.callback("m:background"))
    harness.session.files["car1"] = car_jpeg
    await harness.feed(u.document("car1", len(car_jpeg)))
    await harness.feed(u.callback("nav:confirm"))
    await harness.feed(u.callback("opt:custom"))
    assert await harness.state() == BackgroundStates.reference.state
    harness.session.files["bg"] = car_jpeg
    await harness.feed(u.photo("bg", len(car_jpeg)))
    assert "сжатым" in harness.session.last_text()
    await harness.feed(u.callback("nav:confirm"))
    assert "Изображений: 2" in harness.session.last_text()


async def test_wheels_flow_with_reference_warning(harness: Harness, car_jpeg: bytes) -> None:
    u = harness.updates
    await harness.feed(u.callback("m:wheels"))
    harness.session.files["car1"] = car_jpeg
    await harness.feed(u.document("car1", len(car_jpeg)))
    await harness.feed(u.callback("nav:confirm"))
    assert await harness.state() == WheelStates.reference.state
    harness.session.files["rim"] = car_jpeg  # не диск — должно быть предупреждение
    await harness.feed(u.document("rim", len(car_jpeg)))
    assert "⚠️ Референс" in harness.session.last_text()
    await harness.feed(u.callback("nav:confirm"))
    await harness.feed(u.callback("opt:larger"))
    assert await harness.state() == WheelStates.summary.state
    await harness.feed(u.callback("nav:confirm"))
    async with harness.session_factory() as s:
        job = (await s.execute(select(Job))).scalar_one()
        types = sorted(a.asset_type.value for a in (await s.execute(select(Asset))).scalars())
    assert job.parameters == {"size_mode": "larger"}
    assert types == ["original", "reference"]


async def test_interior_custom_hex_and_parts(harness: Harness, car_jpeg: bytes) -> None:
    u = harness.updates
    await harness.feed(u.callback("m:interior_color"))
    harness.session.files["salon"] = car_jpeg
    await harness.feed(u.document("salon", len(car_jpeg)))
    await harness.feed(u.callback("nav:confirm"))
    await harness.feed(u.callback("opt:custom"))
    assert await harness.state() == InteriorStates.hex.state
    await harness.feed(u.text("not a color"))
    assert "Не похоже на HEX" in harness.session.last_text()
    await harness.feed(u.text("8b4513"))
    assert await harness.state() == InteriorStates.parts.state

    await harness.feed(u.callback("nav:confirm"))
    assert "Выберите хотя бы один элемент" in harness.alerts()
    await harness.feed(u.callback("opt:seats"))
    await harness.feed(u.callback("opt:armrest"))
    await harness.feed(u.callback("opt:armrest"))  # повторное нажатие снимает выбор
    assert (await harness.data())["parts"] == ["seats"]
    await harness.feed(u.callback("nav:confirm"))
    assert "#8B4513" in harness.session.last_text()


async def test_invalid_file_is_rejected(harness: Harness) -> None:
    u = harness.updates
    await harness.feed(u.callback("m:plate"))
    harness.session.files["evil"] = b"MZ\x90\x00" + b"\x00" * 100
    await harness.feed(u.document("evil", 104, mime="application/octet-stream"))
    assert "Это не изображение" in harness.session.last_text()
    assert "original" not in await harness.data()


async def test_concurrency_limit(harness: Harness, car_jpeg: bytes, settings: Settings) -> None:
    u = harness.updates
    harness.session.files["car1"] = car_jpeg
    for _ in range(settings.max_active_jobs_per_user + 1):
        await harness.feed(u.callback("m:plate"))
        await harness.feed(u.document("car1", len(car_jpeg)))
        await harness.feed(u.callback("nav:confirm"))
        await harness.feed(u.callback("nav:confirm"))
    assert len(harness.queue.items) == settings.max_active_jobs_per_user
    assert any("уже есть задания в обработке" in a for a in harness.alerts())


async def test_admin_commands_require_role(harness: Harness) -> None:
    await harness.feed(harness.updates.text("/stats"))
    assert "Недостаточно прав" in harness.session.last_text()
