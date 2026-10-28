from __future__ import annotations

from typing import Any

from app.agent.llm import SupportAgent
from app.agent.tools import ToolContext, ToolRunner
from app.db import Store
from tests.conftest import (
    FakeCatalog,
    FakeKeyCRM,
    FakeNovaPoshta,
    FakeOpenAI,
    FakeTelegram,
    call_response,
    sample_order,
    text_response,
)


def make_runner(store: Store, **fakes: Any) -> tuple[ToolRunner, dict[str, Any]]:
    deps = {
        "keycrm": FakeKeyCRM([sample_order()]),
        "novaposhta": FakeNovaPoshta(),
        "catalog": FakeCatalog(),
        "telegram": FakeTelegram(),
    }
    deps.update(fakes)
    runner = ToolRunner(store=store, **deps)  # type: ignore[arg-type]
    return runner, deps


async def test_agent_runs_tool_and_returns_final_text(store: Store) -> None:
    conv = await store.get_or_create_conversation(None)
    runner, _ = make_runner(store)
    client = FakeOpenAI(
        [
            call_response("r1", "find_orders", {"phone": "097 342 34 55"}),
            text_response("r2", "Ваш заказ №4521 уже в Одессе."),
        ]
    )
    agent = SupportAgent(client=client, tools=runner, model="test")  # type: ignore[arg-type]
    reply = await agent.reply(
        system_prompt="sys",
        history=[],
        user_text="где заказ? 097 342 34 55",
        previous_response_id=None,
        ctx=ToolContext(conversation=conv, transcript=""),
    )
    assert reply.text == "Ваш заказ №4521 уже в Одессе."
    assert reply.response_id == "r2"
    assert reply.tool_calls == [{"name": "find_orders", "args": {"phone": "097 342 34 55"}}]
    assert reply.outcome.client_phone == "+380973423455"
    assert reply.outcome.client_name == "Іван Петренко"
    # Результат инструмента ушёл в модель продолжением того же ответа
    second = client.responses.calls[1]
    assert second["previous_response_id"] == "r1"
    assert second["input"][0]["type"] == "function_call_output"
    assert '"tracking_code": "20450000000001"' in second["input"][0]["output"]


async def test_handoff_marks_conversation_and_notifies(store: Store) -> None:
    conv = await store.get_or_create_conversation(None)
    runner, deps = make_runner(store)
    client = FakeOpenAI(
        [
            call_response(
                "r1",
                "handoff_to_manager",
                {"reason": "тест-драйв", "summary": "Хочет BYD Seal", "client_phone": "0973423455"},
            ),
            text_response("r2", "Передала менеджеру, он ответит здесь."),
        ]
    )
    agent = SupportAgent(client=client, tools=runner, model="test")  # type: ignore[arg-type]
    reply = await agent.reply(
        system_prompt="sys",
        history=[],
        user_text="хочу тест-драйв",
        previous_response_id=None,
        ctx=ToolContext(conversation=conv, transcript="Клиент: хочу тест-драйв"),
    )
    assert reply.outcome.handed_off is True
    updated = await store.get_conversation(conv.id)
    assert updated is not None
    assert updated.handed_off is True
    assert updated.manager_message_id == 4242
    assert updated.client_phone == "+380973423455"
    assert deps["telegram"].notifications[0]["reason"] == "тест-драйв"
    assert deps["keycrm"].leads[0]["phone"] == "+380973423455"


async def test_lost_previous_response_falls_back_to_history(store: Store) -> None:
    conv = await store.get_or_create_conversation(None)
    await store.add_message(conv.id, "user", "привет")
    await store.add_message(conv.id, "assistant", "здравствуйте")
    history = await store.history(conv.id, 10)
    runner, _ = make_runner(store)
    client = FakeOpenAI([text_response("r9", "продолжаем")])
    original = client.responses.create

    async def create(**kwargs: Any) -> Any:
        if kwargs.get("previous_response_id"):
            import openai

            raise openai.NotFoundError(
                "Previous response with id 'old' not found",
                response=_fake_http_response(),
                body=None,
            )
        return await original(**kwargs)

    client.responses.create = create  # type: ignore[method-assign]
    agent = SupportAgent(client=client, tools=runner, model="test")  # type: ignore[arg-type]
    reply = await agent.reply(
        system_prompt="sys",
        history=history,
        user_text="ещё вопрос",
        previous_response_id="old",
        ctx=ToolContext(conversation=conv, transcript=""),
    )
    assert reply.text == "продолжаем"
    sent = client.responses.calls[0]["input"]
    assert [m["role"] for m in sent] == ["user", "assistant", "user"]


async def test_handoff_without_delivery_path_keeps_ai_answering(store: Store) -> None:
    conv = await store.get_or_create_conversation(None)

    class SilentTelegram(FakeTelegram):
        async def notify_handoff(self, conv: Any, **kwargs: Any) -> int | None:
            return None

    runner, _ = make_runner(store, telegram=SilentTelegram(), keycrm=FakeKeyCRM(configured=False))
    client = FakeOpenAI(
        [
            call_response("r1", "handoff_to_manager", {"reason": "жалоба", "summary": "брак"}),
            text_response("r2", "Извините, напишите на почту."),
        ]
    )
    agent = SupportAgent(client=client, tools=runner, model="test")  # type: ignore[arg-type]
    reply = await agent.reply(
        system_prompt="sys",
        history=[],
        user_text="хочу пожаловаться",
        previous_response_id=None,
        ctx=ToolContext(conversation=conv, transcript=""),
    )
    assert reply.outcome.handed_off is False
    updated = await store.get_conversation(conv.id)
    assert updated is not None and updated.handed_off is False
    output = client.responses.calls[1]["input"][0]["output"]
    assert '"manager_notified": false' in output


async def test_streaming_emits_status_and_deltas(store: Store) -> None:
    conv = await store.get_or_create_conversation(None)
    runner, _ = make_runner(store)
    client = FakeOpenAI(
        [
            call_response("r1", "track_parcel", {"ttn": "20450000000001"}),
            text_response("r2", "Посылка в пути.", deltas=["Посылка ", "в пути."]),
        ]
    )
    agent = SupportAgent(client=client, tools=runner, model="test")  # type: ignore[arg-type]
    events: list[str] = []

    async def on_delta(chunk: str) -> None:
        events.append(f"delta:{chunk}")

    async def on_status(tool: str) -> None:
        events.append(f"status:{tool}")

    reply = await agent.reply(
        system_prompt="sys",
        history=[],
        user_text="где посылка 20450000000001",
        previous_response_id=None,
        ctx=ToolContext(conversation=conv, transcript=""),
        on_delta=on_delta,
        on_status=on_status,
    )
    assert reply.text == "Посылка в пути."
    assert events == ["status:track_parcel", "delta:Посылка ", "delta:в пути."]


def _fake_http_response() -> Any:
    import httpx

    return httpx.Response(404, request=httpx.Request("POST", "https://api.openai.com/v1/responses"))
