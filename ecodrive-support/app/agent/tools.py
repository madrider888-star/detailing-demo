"""Инструменты консультанта: схемы для модели и их выполнение."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.logging import get_logger
from app.db import Conversation, Store
from app.integrations.cscart import CatalogClient
from app.integrations.keycrm import KeyCRMClient, normalize_phone
from app.integrations.novaposhta import NovaPoshtaClient, normalize_ttn
from app.integrations.telegram import ManagerTelegram, TelegramError

log = get_logger(__name__)

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "find_orders",
        "description": (
            "Найти заказы клиента в CRM по номеру телефона. Вызывать только после того, как "
            "клиент сам назвал свой телефон. Возвращает последние заказы: статус, товары, "
            "номер накладной (tracking_code) и службу доставки."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {"type": "string", "description": "Телефон клиента в любом формате"}
            },
            "required": ["phone"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "track_parcel",
        "description": (
            "Статус посылки Новой Почты по номеру накладной (14 цифр). Если номер взят из "
            "заказа, передай и телефон клиента."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ttn": {"type": "string", "description": "Номер накладной, 14 цифр"},
                "phone": {"type": "string", "description": "Телефон получателя, если известен"},
            },
            "required": ["ttn"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search_catalog",
        "description": (
            "Поиск по каталогу сайта: автомобили, запчасти, аксессуары, зарядные устройства, "
            "электросамокаты. Возвращает название, цену, наличие и ссылку на товар."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Короткий запрос: модель или тип товара"}
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "handoff_to_manager",
        "description": (
            "Передать диалог живому менеджеру: жалоба, возврат, покупка, тест-драйв, просьба "
            "позвать человека или вопрос, на который ты не можешь ответить. После вызова ты "
            "больше не отвечаешь — менеджер напишет клиенту в этот же чат."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Причина одной фразой"},
                "summary": {
                    "type": "string",
                    "description": "Суть для менеджера: что хочет клиент, что уже выяснено",
                },
                "client_name": {"type": "string", "description": "Имя клиента, если назвал"},
                "client_phone": {"type": "string", "description": "Телефон клиента, если назвал"},
            },
            "required": ["reason", "summary"],
            "additionalProperties": False,
        },
    },
]


@dataclass
class ToolContext:
    conversation: Conversation
    transcript: str  # последние сообщения диалога — для менеджера


@dataclass
class ToolOutcome:
    """Что инструменты узнали за один ответ модели — API сохранит это в диалог."""

    handed_off: bool = False
    client_phone: str | None = None
    client_name: str | None = None


class ToolRunner:
    def __init__(
        self,
        *,
        store: Store,
        keycrm: KeyCRMClient,
        novaposhta: NovaPoshtaClient,
        catalog: CatalogClient,
        telegram: ManagerTelegram,
    ) -> None:
        self._store = store
        self._keycrm = keycrm
        self._novaposhta = novaposhta
        self._catalog = catalog
        self._telegram = telegram

    async def run(
        self, name: str, args: dict[str, Any], ctx: ToolContext, outcome: ToolOutcome
    ) -> str:
        """Результат инструмента для модели — всегда JSON-строка, ошибки тоже внутри."""
        handler = getattr(self, f"_{name}", None)
        result: dict[str, Any]
        try:
            if handler is None:
                result = {"error": f"Неизвестный инструмент {name}"}
            else:
                result = await handler(args, ctx, outcome)
        except httpx.HTTPError as exc:
            log.warning("tool.http_error", tool=name, error=str(exc))
            result = {
                "error": "Сервис временно недоступен. Извинись и предложи передать менеджеру."
            }
        except ValueError as exc:
            result = {"error": str(exc)}
        log.info("tool.called", tool=name, conversation_id=ctx.conversation.id)
        return json.dumps(result, ensure_ascii=False)

    async def _find_orders(
        self, args: dict[str, Any], ctx: ToolContext, outcome: ToolOutcome
    ) -> dict[str, Any]:
        phone = normalize_phone(str(args.get("phone", "")))
        if phone is None:
            return {"error": "Телефон не распознан. Попроси клиента написать номер ещё раз."}
        if not self._keycrm.configured:
            return {
                "error": "CRM не подключена: заказы искать нельзя. Предложи передать менеджеру."
            }
        orders = await self._keycrm.find_orders_by_phone(phone)
        outcome.client_phone = phone
        if orders and orders[0].buyer_name:
            outcome.client_name = orders[0].buyer_name
        if not orders:
            return {
                "orders": [],
                "note": (
                    "Заказов с этим телефоном нет: уточни номер, спроси ТТН или зови менеджера."
                ),
            }
        return {"orders": [order.as_dict() for order in orders]}

    async def _track_parcel(
        self, args: dict[str, Any], ctx: ToolContext, outcome: ToolOutcome
    ) -> dict[str, Any]:
        ttn = normalize_ttn(str(args.get("ttn", "")))
        if ttn is None:
            return {"error": "Номер накладной — это 14 цифр. Попроси клиента проверить номер."}
        phone = str(
            args.get("phone") or outcome.client_phone or ctx.conversation.client_phone or ""
        )
        parcel = await self._novaposhta.track(ttn, phone)
        if parcel is None:
            return {"error": "Накладная не найдена. Попроси клиента проверить номер."}
        return {"parcel": parcel.as_dict()}

    async def _search_catalog(
        self, args: dict[str, Any], ctx: ToolContext, outcome: ToolOutcome
    ) -> dict[str, Any]:
        products = await self._catalog.search(str(args.get("query", "")))
        if not products:
            return {
                "products": [],
                "note": "Ничего не найдено. Не выдумывай товары: уточни запрос или зови менеджера.",
            }
        return {"products": [product.as_dict() for product in products]}

    async def _handoff_to_manager(
        self, args: dict[str, Any], ctx: ToolContext, outcome: ToolOutcome
    ) -> dict[str, Any]:
        conv = ctx.conversation
        phone = (
            normalize_phone(str(args.get("client_phone") or ""))
            or outcome.client_phone
            or conv.client_phone
        )
        name = str(args.get("client_name") or "").strip() or outcome.client_name or conv.client_name
        reason = str(args.get("reason") or "запрос клиента").strip()
        summary = str(args.get("summary") or "").strip()
        conv.client_phone, conv.client_name = phone, name
        outcome.client_phone, outcome.client_name = phone, name

        message_id: int | None = None
        try:
            message_id = await self._telegram.notify_handoff(
                conv, reason=reason, summary=summary, transcript=ctx.transcript
            )
        except (httpx.HTTPError, TelegramError) as exc:
            log.warning("handoff.telegram_failed", error=str(exc))

        lead_id: int | None = None
        try:
            lead_id = await self._keycrm.create_lead(
                title=f"Чат на сайте: {reason}"[:120],
                phone=phone,
                full_name=name,
                comment=f"{summary}\n\nПереписка:\n{ctx.transcript}",
            )
        except httpx.HTTPError as exc:
            log.warning("handoff.keycrm_failed", error=str(exc))

        # Диалог уходит к менеджеру только если его реально кто-то получил; иначе ИИ
        # продолжает отвечать сам, а не оставляет клиента в тишине.
        notified = message_id is not None or lead_id is not None
        await self._store.update_conversation(
            conv.id,
            handed_off=notified,
            manager_message_id=message_id,
            client_phone=phone,
            client_name=name,
        )
        await self._store.add_message(
            conv.id,
            "system",
            f"Передано менеджеру: {reason}" if notified else f"Не удалось передать: {reason}",
            meta={"lead_id": lead_id, "telegram_message_id": message_id},
        )
        outcome.handed_off = notified
        if notified:
            note = "Скажи клиенту, что менеджер ответит здесь, в этом чате"
            note += " или по телефону." if phone else "."
        else:
            note = (
                "Уведомить менеджеров не удалось. Извинись, предложи написать на "
                "dopomoga@ecodrive.in.ua или оставить телефон, и продолжай помогать сам."
            )
        return {"ok": notified, "manager_notified": notified, "note": note}
