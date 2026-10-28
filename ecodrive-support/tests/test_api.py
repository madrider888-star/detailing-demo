from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from app.agent.llm import AgentError, AgentReply
from app.agent.tools import ToolOutcome
from app.api.main import RateLimiter, Services, app, detect_lang
from app.core.config import Settings
from app.db import Store
from tests.conftest import FakeTelegram


class FakeAgent:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.fail = False
        self.outcome = ToolOutcome()

    async def reply(self, **kwargs: Any) -> AgentReply:
        self.calls.append(kwargs)
        if self.fail:
            raise AgentError("down")
        if kwargs.get("on_status"):
            await kwargs["on_status"]("find_orders")
        if kwargs.get("on_delta"):
            for chunk in ("Ответ ", "консультанта"):
                await kwargs["on_delta"](chunk)
        return AgentReply(text="Ответ консультанта", response_id="resp-1", outcome=self.outcome)


@pytest.fixture
async def api(store: Store) -> AsyncIterator[tuple[httpx.AsyncClient, FakeAgent, FakeTelegram]]:
    agent = FakeAgent()
    telegram = FakeTelegram()
    app.state.services = Services(
        settings=Settings(_env_file=None),  # type: ignore[call-arg]
        store=store,
        agent=agent,  # type: ignore[arg-type]
        telegram=telegram,  # type: ignore[arg-type]
        closeables=[],
        limiter=RateLimiter(limit=5),
        prompts={"uk": "uk-prompt", "ru": "ru-prompt"},
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, agent, telegram


def test_detect_lang() -> None:
    assert detect_lang("ru", None) == "ru"
    assert detect_lang(None, "https://ecodrive.in.ua/ru/auto/") == "ru"
    assert detect_lang(None, "https://ecodrive.in.ua/auto/") == "uk"


async def test_chat_creates_session_and_replies(api: Any, store: Store) -> None:
    client, agent, _ = api
    r = await client.post(
        "/api/chat", json={"message": "привет", "page_url": "https://ecodrive.in.ua/ru/"}
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["reply"] == "Ответ консультанта"
    assert data["handed_off"] is False
    assert agent.calls[0]["system_prompt"] == "ru-prompt"
    conv = await store.get_conversation(data["session_id"])
    assert conv is not None and conv.openai_response_id == "resp-1"

    # Та же сессия: история передаётся, новые сообщения видны через polling
    r2 = await client.post("/api/chat", json={"session_id": data["session_id"], "message": "ещё"})
    assert r2.status_code == 200
    assert len(agent.calls[1]["history"]) == 2
    r3 = await client.get(f"/api/chat/{data['session_id']}/messages?after=0")
    assert [m["role"] for m in r3.json()["messages"]] == ["assistant", "assistant"]


async def test_handed_off_conversation_relays_to_manager(api: Any, store: Store) -> None:
    client, agent, telegram = api
    first = (await client.post("/api/chat", json={"message": "хочу менеджера"})).json()
    await store.update_conversation(first["session_id"], handed_off=True, manager_message_id=1)
    r = await client.post(
        "/api/chat", json={"session_id": first["session_id"], "message": "вы тут?"}
    )
    assert r.json()["reply"] is None and r.json()["handed_off"] is True
    assert telegram.relayed == ["вы тут?"]
    assert len(agent.calls) == 1  # ИИ больше не отвечает


async def test_agent_failure_returns_fallback(api: Any) -> None:
    client, agent, _ = api
    agent.fail = True
    r = await client.post("/api/chat", json={"message": "привіт"})
    assert r.status_code == 200
    assert "менеджер" in r.json()["reply"]


async def test_rate_limit_and_validation(api: Any) -> None:
    client, _, _ = api
    assert (await client.post("/api/chat", json={"message": ""})).status_code == 422
    assert (await client.get("/api/chat/not-a-session/messages")).status_code == 404
    statuses = [
        (await client.post("/api/chat", json={"message": "x"})).status_code for _ in range(6)
    ]
    assert statuses[-1] == 429


async def test_chat_stream_sends_status_deltas_and_done(api: Any) -> None:
    client, _, _ = api
    import json

    async with client.stream(
        "POST", "/api/chat/stream", json={"message": "где заказ", "lang": "ru"}
    ) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        raw = "".join([chunk async for chunk in r.aiter_text()])
    events = [json.loads(p[6:]) for p in raw.split("\n\n") if p.startswith("data: ")]
    assert [e["type"] for e in events] == ["session", "status", "delta", "delta", "done"]
    assert events[1]["text"] == "Смотрю заказ…"
    assert events[-1]["reply"] == "Ответ консультанта"
    assert events[-1]["session_id"] == events[0]["session_id"]


async def test_widget_injects_base_url(api: Any) -> None:
    client, _, _ = api
    r = await client.get(
        "/widget.js", headers={"host": "chat.example.com", "x-forwarded-proto": "https"}
    )
    assert r.status_code == 200
    assert 'var BASE = "https://chat.example.com"' in r.text
    assert "__BOT_NAME__" not in r.text
