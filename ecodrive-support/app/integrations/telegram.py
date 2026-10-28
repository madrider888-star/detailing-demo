"""Telegram-бот менеджеров: уведомление о передаче диалога и ответы клиенту из группы.

Менеджер отвечает клиенту обычным Reply на сообщение бота — ответ попадает в чат на сайте.
`/done` в ответ на то же сообщение возвращает диалог консультанту-ИИ.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx

from app.core.logging import get_logger
from app.db import Conversation, Store

log = get_logger(__name__)

_MARKER_RE = re.compile(r"#conv:([0-9a-f]{32})")


class TelegramError(RuntimeError):
    pass


class ManagerTelegram:
    def __init__(
        self,
        token: str,
        managers_chat_id: int | None,
        store: Store,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 35.0,
    ) -> None:
        self._token = token
        self._chat_id = managers_chat_id
        self._store = store
        self._client = client or httpx.AsyncClient(timeout=timeout)

    @property
    def configured(self) -> bool:
        return bool(self._token) and self._chat_id is not None

    async def close(self) -> None:
        await self._client.aclose()

    async def _call(self, method: str, **params: Any) -> Any:
        response = await self._client.post(
            f"https://api.telegram.org/bot{self._token}/{method}", json=params
        )
        data = response.json()
        if not data.get("ok"):
            raise TelegramError(f"{method}: {data.get('description', response.status_code)}")
        return data["result"]

    # --- исходящее: сайт → менеджеры ---

    async def notify_handoff(
        self, conv: Conversation, *, reason: str, summary: str, transcript: str
    ) -> int | None:
        """Сообщение в группу менеджеров; возвращает его id для ответов (Reply)."""
        if not self.configured:
            return None
        contact = " · ".join(p for p in (conv.client_name, conv.client_phone) if p)
        text = (
            "🆕 Обращение с сайта\n"
            f"Причина: {reason}\n"
            + (f"Клиент: {contact}\n" if contact else "")
            + f"\n{summary}\n\n"
            f"— Переписка —\n{transcript}\n\n"
            "Ответьте на это сообщение (Reply) — клиент увидит ответ в чате на сайте.\n"
            "/done в ответ — вернуть диалог консультанту.\n"
            f"#conv:{conv.id}"
        )
        result = await self._call("sendMessage", chat_id=self._chat_id, text=text[:4000])
        return int(result["message_id"])

    async def relay_client_message(self, conv: Conversation, text: str) -> None:
        """Новое сообщение клиента после передачи — в ту же ветку группы."""
        if not self.configured:
            return
        params: dict[str, Any] = {
            "chat_id": self._chat_id,
            "text": f"💬 Клиент: {text}\n#conv:{conv.id}"[:4000],
        }
        if conv.manager_message_id:
            params["reply_to_message_id"] = conv.manager_message_id
            params["allow_sending_without_reply"] = True
        await self._call("sendMessage", **params)

    # --- входящее: менеджеры → сайт ---

    async def run_polling(self, stop: asyncio.Event) -> None:
        """Long polling getUpdates до события stop. Ошибки сети — пауза и повтор."""
        offset: int | None = None
        log.info("telegram.polling_started", chat_id=self._chat_id)
        while not stop.is_set():
            try:
                updates = await self._call(
                    "getUpdates", offset=offset, timeout=25, allowed_updates=["message"]
                )
            except (httpx.HTTPError, TelegramError, ValueError) as exc:
                log.warning("telegram.poll_failed", error=str(exc))
                await asyncio.sleep(5)
                continue
            for update in updates:
                offset = int(update["update_id"]) + 1
                try:
                    await self.handle_message(update.get("message"))
                except Exception:
                    log.exception("telegram.update_failed", update_id=update.get("update_id"))

    async def handle_message(self, msg: dict[str, Any] | None) -> None:
        if not msg or msg.get("chat", {}).get("id") != self._chat_id:
            return
        reply = msg.get("reply_to_message")
        text = (msg.get("text") or msg.get("caption") or "").strip()
        if not reply or not text:
            return
        marker = _MARKER_RE.search(reply.get("text") or "")
        if marker is None:
            return
        conv = await self._store.get_conversation(marker.group(1))
        if conv is None:
            return
        sender = msg.get("from") or {}
        manager = sender.get("first_name") or sender.get("username") or "менеджер"

        if text.split()[0].lower().startswith("/done"):
            await self._store.update_conversation(
                conv.id, handed_off=False, openai_response_id=None
            )
            await self._store.add_message(
                conv.id, "system", f"Менеджер {manager} вернул диалог консультанту"
            )
            await self._react(msg, "👌")
            return

        await self._store.add_message(conv.id, "manager", text, meta={"manager": manager})
        if not conv.handed_off:
            # Менеджер вмешался сам — дальше отвечает он, а не ИИ
            await self._store.update_conversation(conv.id, handed_off=True)
        await self._react(msg, "👍")

    async def _react(self, msg: dict[str, Any], emoji: str) -> None:
        try:
            await self._call(
                "setMessageReaction",
                chat_id=self._chat_id,
                message_id=msg["message_id"],
                reaction=[{"type": "emoji", "emoji": emoji}],
            )
        except (httpx.HTTPError, TelegramError):
            pass  # реакция — только подтверждение для менеджера, без неё можно
