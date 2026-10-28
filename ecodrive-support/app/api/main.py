"""HTTP-сервис: чат для виджета, сам виджет, тестовая страница и служебные ручки."""

from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.agent.llm import SupportAgent
from app.agent.prompt import build_system_prompt, load_knowledge
from app.agent.tools import ToolContext, ToolRunner
from app.core.config import PROJECT_ROOT, Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.db import Conversation, Message, Store
from app.integrations.cscart import CatalogClient
from app.integrations.keycrm import KeyCRMClient
from app.integrations.novaposhta import NovaPoshtaClient
from app.integrations.telegram import ManagerTelegram, TelegramError

log = get_logger(__name__)

WIDGET_PATH = PROJECT_ROOT / "widget" / "widget.js"
DEMO_PATH = PROJECT_ROOT / "widget" / "demo.html"
SESSION_PATTERN = r"^[0-9a-f]{32}$"

FALLBACK_REPLY = {
    "uk": (
        "Вибачте, зараз не можу відповісти. Напишіть, будь ласка, за хвилину або залиште "
        "номер телефону — менеджер звʼяжеться з вами."
    ),
    "ru": (
        "Извините, сейчас не могу ответить. Напишите, пожалуйста, через минуту или оставьте "
        "номер телефона — менеджер свяжется с вами."
    ),
}


class RateLimiter:
    """Скользящее окно: не больше `limit` событий за `window` секунд на ключ."""

    def __init__(self, limit: int, window: float = 60.0) -> None:
        self._limit = limit
        self._window = window
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self._window:
            hits.popleft()
        if len(hits) >= self._limit:
            return False
        hits.append(now)
        if len(self._hits) > 10_000:  # не копим ключи вечно
            for stale in [k for k, v in self._hits.items() if not v or now - v[-1] > self._window]:
                del self._hits[stale]
        return True


@dataclass
class Services:
    settings: Settings
    store: Store
    agent: SupportAgent
    telegram: ManagerTelegram
    closeables: list[Any]
    limiter: RateLimiter
    prompts: dict[str, str]
    locks: dict[str, asyncio.Lock] = field(default_factory=lambda: defaultdict(asyncio.Lock))
    poll_task: asyncio.Task[None] | None = None
    stop: asyncio.Event = field(default_factory=asyncio.Event)


def build_services(settings: Settings) -> Services:
    store = Store(settings.database_url)
    keycrm = KeyCRMClient(
        settings.keycrm_api_key.get_secret_value(),
        base_url=settings.keycrm_base_url,
        pipeline_id=settings.keycrm_pipeline_id,
        source_id=settings.keycrm_source_id,
    )
    novaposhta = NovaPoshtaClient(settings.novaposhta_api_key.get_secret_value())
    catalog = CatalogClient(
        settings.cscart_base_url,
        api_email=settings.cscart_api_email,
        api_key=settings.cscart_api_key.get_secret_value(),
    )
    telegram = ManagerTelegram(
        settings.telegram_bot_token.get_secret_value(), settings.telegram_managers_chat_id, store
    )
    tools = ToolRunner(
        store=store, keycrm=keycrm, novaposhta=novaposhta, catalog=catalog, telegram=telegram
    )
    client = AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value() or "missing",
        base_url=settings.openai_base_url,
        timeout=settings.openai_timeout_seconds,
        max_retries=2,
    )
    agent = SupportAgent(
        client=client,
        tools=tools,
        model=settings.openai_model,
        reasoning_effort=settings.openai_reasoning_effort,
        max_output_tokens=settings.max_output_tokens,
        max_tool_rounds=settings.max_tool_rounds,
    )
    knowledge = load_knowledge(settings.knowledge_path)
    prompts = {
        lang: build_system_prompt(
            bot_name=settings.bot_name,
            shop_name=settings.shop_name,
            shop_site=settings.shop_site,
            knowledge=knowledge,
            default_lang=lang,
        )
        for lang in ("uk", "ru")
    }
    return Services(
        settings=settings,
        store=store,
        agent=agent,
        telegram=telegram,
        closeables=[keycrm, novaposhta, catalog, telegram, store],
        limiter=RateLimiter(settings.rate_limit_per_minute),
        prompts=prompts,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format, settings.secret_values())
    services = build_services(settings)
    await services.store.init()
    if services.telegram.configured and settings.telegram_polling:
        services.poll_task = asyncio.create_task(services.telegram.run_polling(services.stop))
    app.state.services = services
    log.info(
        "support.started",
        model=settings.openai_model,
        keycrm=bool(settings.keycrm_api_key.get_secret_value()),
        telegram=services.telegram.configured,
    )
    yield
    services.stop.set()
    if services.poll_task:
        services.poll_task.cancel()
        await asyncio.gather(services.poll_task, return_exceptions=True)
    for item in services.closeables:
        await item.close()


app = FastAPI(title="ECODRIVE support", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    max_age=3600,
)


def _services(request: Request) -> Services:
    return request.app.state.services  # type: ignore[no-any-return]


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, pattern=SESSION_PATTERN)
    message: str = Field(min_length=1, max_length=2000)
    page_url: str | None = Field(default=None, max_length=500)
    lang: str | None = Field(default=None, max_length=8)


class ChatMessage(BaseModel):
    id: int
    role: str
    text: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str | None
    handed_off: bool
    last_id: int


class MessagesResponse(BaseModel):
    messages: list[ChatMessage]
    handed_off: bool


def detect_lang(lang: str | None, page_url: str | None) -> str:
    if (lang or "").lower().startswith("ru") or "/ru/" in (page_url or ""):
        return "ru"
    return "uk"


def _transcript(messages: list[Message], bot_name: str, limit: int = 12) -> str:
    names = {"user": "Клиент", "assistant": bot_name, "manager": "Менеджер", "system": "Система"}
    lines = [f"{names.get(m.role, m.role)}: {m.content}" for m in messages[-limit:]]
    return "\n".join(lines)[:2500]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/widget.js")
async def widget(request: Request) -> Response:
    services = _services(request)
    base = services.settings.public_base_url.rstrip("/")
    if not base:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        base = f"{scheme}://{request.headers.get('host', request.url.netloc)}"
    source = WIDGET_PATH.read_text(encoding="utf-8")
    source = source.replace("__BASE_URL__", base).replace(
        "__BOT_NAME__", services.settings.bot_name
    )
    return Response(
        source,
        media_type="application/javascript; charset=utf-8",
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.get("/demo", response_class=HTMLResponse)
async def demo() -> str:
    return DEMO_PATH.read_text(encoding="utf-8")


# Что показывать клиенту, пока работает инструмент (потоковый режим)
STATUS_TEXT = {
    "uk": {
        "find_orders": "Дивлюся замовлення…",
        "track_parcel": "Перевіряю посилку в Новій Пошті…",
        "search_catalog": "Шукаю в каталозі…",
        "handoff_to_manager": "Передаю менеджеру…",
    },
    "ru": {
        "find_orders": "Смотрю заказ…",
        "track_parcel": "Проверяю посылку в Новой Почте…",
        "search_catalog": "Ищу в каталоге…",
        "handoff_to_manager": "Передаю менеджеру…",
    },
}


async def _prepare(payload: ChatRequest, request: Request) -> tuple[Services, Conversation, str]:
    """Общее для обоих эндпоинтов чата: лимиты, валидация, диалог."""
    services = _services(request)
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    if not services.limiter.allow(f"ip:{client_ip}") or (
        payload.session_id and not services.limiter.allow(f"s:{payload.session_id}")
    ):
        raise HTTPException(status_code=429, detail="Too many messages, slow down")

    text = payload.message.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Empty message")
    lang = detect_lang(payload.lang, payload.page_url)
    conv = await services.store.get_or_create_conversation(
        payload.session_id, lang=lang, page_url=payload.page_url
    )
    return services, conv, text


async def _chat_events(
    services: Services, conv: Conversation, text: str, *, stream: bool
) -> AsyncIterator[dict[str, Any]]:
    """События ответа: `status` и `delta` (только при stream) и завершающий `done`."""
    store = services.store
    history = await store.history(conv.id, services.settings.history_messages)
    user_msg = await store.add_message(conv.id, "user", text)
    done: dict[str, Any] = {
        "type": "done",
        "session_id": conv.id,
        "reply": None,
        "handed_off": True,
        "last_id": user_msg.id,
    }

    if conv.handed_off:
        try:
            await services.telegram.relay_client_message(conv, text)
        except (httpx.HTTPError, TelegramError) as exc:
            log.warning("relay.failed", conversation_id=conv.id, error=str(exc))
        yield done
        return

    lang = conv.lang if conv.lang in services.prompts else "uk"
    ctx = ToolContext(
        conversation=conv,
        transcript=_transcript([*history, user_msg], services.settings.bot_name),
    )
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def on_delta(chunk: str) -> None:
        await queue.put({"type": "delta", "text": chunk})

    async def on_status(tool: str) -> None:
        await queue.put({"type": "status", "text": STATUS_TEXT[lang].get(tool, "…")})

    task = asyncio.create_task(
        services.agent.reply(
            system_prompt=services.prompts[lang],
            history=history,
            user_text=text,
            previous_response_id=conv.openai_response_id,
            ctx=ctx,
            on_delta=on_delta if stream else None,
            on_status=on_status if stream else None,
        )
    )
    task.add_done_callback(lambda _: queue.put_nowait(None))
    while (event := await queue.get()) is not None:
        yield event

    try:
        reply = task.result()
    except Exception:
        log.exception("agent.failed", conversation_id=conv.id)
        fallback = FALLBACK_REPLY.get(conv.lang, FALLBACK_REPLY["uk"])
        msg = await store.add_message(conv.id, "assistant", fallback, meta={"fallback": True})
        yield {**done, "reply": fallback, "handed_off": False, "last_id": msg.id}
        return

    msg = await store.add_message(
        conv.id,
        "assistant",
        reply.text,
        meta={"tool_calls": reply.tool_calls} if reply.tool_calls else None,
    )
    fields: dict[str, Any] = {"openai_response_id": reply.response_id}
    if reply.outcome.client_phone:
        fields["client_phone"] = reply.outcome.client_phone
    if reply.outcome.client_name:
        fields["client_name"] = reply.outcome.client_name
    await store.update_conversation(conv.id, **fields)
    yield {**done, "reply": reply.text, "handed_off": reply.outcome.handed_off, "last_id": msg.id}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    services, conv, text = await _prepare(payload, request)
    async with services.locks[conv.id]:
        # Пока ждали очередь, предыдущий запрос мог передать диалог менеджеру
        # или продвинуть openai_response_id — берём свежее состояние.
        fresh = await services.store.get_conversation(conv.id)
        async for event in _chat_events(services, fresh or conv, text, stream=False):
            if event["type"] == "done":
                return ChatResponse(
                    session_id=event["session_id"],
                    reply=event["reply"],
                    handed_off=event["handed_off"],
                    last_id=event["last_id"],
                )
    raise HTTPException(status_code=500, detail="No reply")


def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
async def chat_stream(payload: ChatRequest, request: Request) -> StreamingResponse:
    """Тот же чат, но ответ идёт потоком (SSE): статус инструментов и текст по мере генерации."""
    services, conv, text = await _prepare(payload, request)

    async def generate() -> AsyncIterator[str]:
        yield _sse({"type": "session", "session_id": conv.id})
        async with services.locks[conv.id]:
            fresh = await services.store.get_conversation(conv.id)
            async for event in _chat_events(services, fresh or conv, text, stream=True):
                yield _sse(event)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/chat/{session_id}/messages", response_model=MessagesResponse)
async def messages(
    session_id: str, request: Request, after: int = Query(default=0, ge=0)
) -> MessagesResponse:
    import re

    if not re.fullmatch(SESSION_PATTERN, session_id):
        raise HTTPException(status_code=404, detail="Unknown session")
    services = _services(request)
    conv = await services.store.get_conversation(session_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Unknown session")
    rows = await services.store.messages_after(session_id, after, ("assistant", "manager"))
    return MessagesResponse(
        messages=[ChatMessage(id=m.id, role=m.role, text=m.content) for m in rows],
        handed_off=conv.handed_off,
    )
