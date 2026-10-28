"""Цикл общения с моделью (OpenAI Responses API) с вызовом инструментов и потоковым выводом."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import openai
from openai import AsyncOpenAI

from app.agent.tools import TOOL_SCHEMAS, ToolContext, ToolOutcome, ToolRunner
from app.core.logging import get_logger
from app.db import Message

log = get_logger(__name__)

# Колбэки потокового режима: кусок текста ответа / имя инструмента перед его запуском
DeltaCallback = Callable[[str], Awaitable[None]]
StatusCallback = Callable[[str], Awaitable[None]]


class AgentError(RuntimeError):
    """Модель недоступна или не дала ответа — API покажет клиенту запасной текст."""


@dataclass
class AgentReply:
    text: str
    response_id: str | None
    outcome: ToolOutcome
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


def history_to_input(messages: list[Message]) -> list[dict[str, Any]]:
    """История диалога в формате Responses API. Ответы менеджера — как реплики ассистента."""
    items: list[dict[str, Any]] = []
    for msg in messages:
        if msg.role == "user":
            items.append({"role": "user", "content": msg.content})
        elif msg.role == "assistant":
            items.append({"role": "assistant", "content": msg.content})
        elif msg.role == "manager":
            items.append({"role": "assistant", "content": f"[Ответ менеджера] {msg.content}"})
        elif msg.role == "system":
            items.append({"role": "developer", "content": f"Событие: {msg.content}"})
    return items


class SupportAgent:
    def __init__(
        self,
        *,
        client: AsyncOpenAI,
        tools: ToolRunner,
        model: str,
        reasoning_effort: str = "low",
        max_output_tokens: int = 700,
        max_tool_rounds: int = 5,
    ) -> None:
        self._client = client
        self._tools = tools
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._max_output_tokens = max_output_tokens
        self._max_tool_rounds = max_tool_rounds

    async def reply(
        self,
        *,
        system_prompt: str,
        history: list[Message],
        user_text: str,
        previous_response_id: str | None,
        ctx: ToolContext,
        on_delta: DeltaCallback | None = None,
        on_status: StatusCallback | None = None,
    ) -> AgentReply:
        """Ответ модели. С `on_delta` текст отдаётся по мере генерации (потоковый режим)."""
        outcome = ToolOutcome()
        calls_log: list[dict[str, Any]] = []
        user_item = {"role": "user", "content": user_text}

        # Продолжаем серверный диалог OpenAI, если он есть; иначе отправляем историю целиком.
        if previous_response_id:
            try:
                response = await self._create(
                    system_prompt, [user_item], previous_response_id, on_delta
                )
            except AgentError as exc:
                if not exc.args or "not found" not in str(exc.args[0]).lower():
                    raise
                log.info("agent.previous_response_lost", previous_response_id=previous_response_id)
                response = await self._create(
                    system_prompt, [*history_to_input(history), user_item], None, on_delta
                )
        else:
            response = await self._create(
                system_prompt, [*history_to_input(history), user_item], None, on_delta
            )

        text_parts = [(response.output_text or "").strip()]
        for _ in range(self._max_tool_rounds):
            calls = [
                item for item in response.output if getattr(item, "type", "") == "function_call"
            ]
            if not calls:
                break
            outputs: list[dict[str, Any]] = []
            for call in calls:
                try:
                    args = json.loads(call.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                if on_status is not None:
                    await on_status(call.name)
                result = await self._tools.run(call.name, args, ctx, outcome)
                calls_log.append({"name": call.name, "args": args})
                outputs.append(
                    {"type": "function_call_output", "call_id": call.call_id, "output": result}
                )
            response = await self._create(system_prompt, outputs, response.id, on_delta)
            text_parts.append((response.output_text or "").strip())

        text = "\n\n".join(part for part in text_parts if part)
        if not text:
            raise AgentError("Модель вернула пустой ответ")
        return AgentReply(text=text, response_id=response.id, outcome=outcome, tool_calls=calls_log)

    async def _create(
        self,
        system_prompt: str,
        input_items: list[dict[str, Any]],
        previous_response_id: str | None,
        on_delta: DeltaCallback | None,
    ) -> Any:
        params: dict[str, Any] = {
            "model": self._model,
            "instructions": system_prompt,
            "input": input_items,
            "tools": TOOL_SCHEMAS,
            "reasoning": {"effort": self._reasoning_effort},
            "max_output_tokens": self._max_output_tokens,
            "previous_response_id": previous_response_id,
        }
        try:
            if on_delta is None:
                return await self._client.responses.create(**params)
            async with self._client.responses.stream(**params) as stream:
                async for event in stream:
                    delta = getattr(event, "delta", None)
                    if event.type == "response.output_text.delta" and isinstance(delta, str):
                        await on_delta(delta)
                return await stream.get_final_response()
        except openai.APIError as exc:
            status = getattr(exc, "status_code", None)
            log.warning("agent.openai_error", error=str(exc), status=status)
            raise AgentError(str(exc)) from exc
