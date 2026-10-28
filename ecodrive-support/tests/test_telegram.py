from __future__ import annotations

import json
from typing import Any

import httpx

from app.db import Store
from app.integrations.telegram import ManagerTelegram

CHAT_ID = -100123


def make_client(calls: list[dict[str, Any]]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content or b"{}")
        payload["_method"] = request.url.path.rsplit("/", 1)[-1]
        calls.append(payload)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 55}})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_manager_reply_is_stored_and_takes_over(store: Store) -> None:
    conv = await store.get_or_create_conversation(None)
    calls: list[dict[str, Any]] = []
    tg = ManagerTelegram("t", CHAT_ID, store, client=make_client(calls))

    await tg.handle_message(
        {
            "message_id": 10,
            "chat": {"id": CHAT_ID},
            "from": {"first_name": "Олег"},
            "text": "Добрый день, посылка будет завтра",
            "reply_to_message": {"message_id": 9, "text": f"🆕 Обращение\n#conv:{conv.id}"},
        }
    )
    history = await store.history(conv.id, 10)
    assert [(m.role, m.content) for m in history] == [
        ("manager", "Добрый день, посылка будет завтра")
    ]
    assert history[0].meta == {"manager": "Олег"}
    updated = await store.get_conversation(conv.id)
    assert updated is not None and updated.handed_off is True
    assert calls[-1]["_method"] == "setMessageReaction"


async def test_done_returns_conversation_to_ai(store: Store) -> None:
    conv = await store.get_or_create_conversation(None)
    await store.update_conversation(conv.id, handed_off=True, openai_response_id="r1")
    tg = ManagerTelegram("t", CHAT_ID, store, client=make_client([]))
    await tg.handle_message(
        {
            "message_id": 11,
            "chat": {"id": CHAT_ID},
            "text": "/done",
            "reply_to_message": {"message_id": 9, "text": f"#conv:{conv.id}"},
        }
    )
    updated = await store.get_conversation(conv.id)
    assert updated is not None
    assert updated.handed_off is False and updated.openai_response_id is None


async def test_messages_from_other_chats_are_ignored(store: Store) -> None:
    conv = await store.get_or_create_conversation(None)
    tg = ManagerTelegram("t", CHAT_ID, store, client=make_client([]))
    await tg.handle_message(
        {
            "message_id": 12,
            "chat": {"id": 1},
            "text": "spam",
            "reply_to_message": {"message_id": 9, "text": f"#conv:{conv.id}"},
        }
    )
    assert await store.history(conv.id, 10) == []
