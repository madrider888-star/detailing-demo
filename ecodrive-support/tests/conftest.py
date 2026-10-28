"""Общие фикстуры: база в памяти, фейковые OpenAI и интеграции."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from app.db import Store
from app.integrations.keycrm import OrderSummary
from app.integrations.novaposhta import ParcelStatus


@pytest.fixture
async def store(tmp_path: Path) -> AsyncIterator[Store]:
    s = Store(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    await s.init()
    yield s
    await s.close()


def text_response(response_id: str, text: str, deltas: list[str] | None = None) -> Any:
    return SimpleNamespace(id=response_id, output=[], output_text=text, deltas=deltas or [])


class _FakeStream:
    """Имитация `responses.stream`: отдаёт заготовленные дельты и финальный ответ."""

    def __init__(self, response: Any) -> None:
        self._response = response
        self._deltas = iter(getattr(response, "deltas", []))

    async def __aenter__(self) -> _FakeStream:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    def __aiter__(self) -> _FakeStream:
        return self

    async def __anext__(self) -> Any:
        try:
            delta = next(self._deltas)
        except StopIteration:
            raise StopAsyncIteration from None
        return SimpleNamespace(type="response.output_text.delta", delta=delta)

    async def get_final_response(self) -> Any:
        return self._response


def call_response(response_id: str, name: str, args: dict[str, Any], call_id: str = "c1") -> Any:
    call = SimpleNamespace(
        type="function_call", name=name, arguments=json.dumps(args), call_id=call_id
    )
    return SimpleNamespace(id=response_id, output=[call], output_text="")


class FakeResponses:
    def __init__(self, scripted: list[Any]) -> None:
        self.scripted = list(scripted)
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.scripted.pop(0)

    def stream(self, **kwargs: Any) -> _FakeStream:
        self.calls.append(kwargs)
        return _FakeStream(self.scripted.pop(0))


class FakeOpenAI:
    def __init__(self, scripted: list[Any]) -> None:
        self.responses = FakeResponses(scripted)


class FakeKeyCRM:
    def __init__(self, orders: list[OrderSummary] | None = None, configured: bool = True) -> None:
        self.orders = orders or []
        self.configured = configured
        self.leads: list[dict[str, Any]] = []

    async def find_orders_by_phone(self, phone: str, limit: int = 5) -> list[OrderSummary]:
        return self.orders

    async def create_lead(self, **kwargs: Any) -> int | None:
        if not self.configured:
            return None
        self.leads.append(kwargs)
        return 777


class FakeNovaPoshta:
    def __init__(self, parcel: ParcelStatus | None = None) -> None:
        self.parcel = parcel
        self.calls: list[tuple[str, str | None]] = []

    async def track(self, ttn: str, phone: str | None = None) -> ParcelStatus | None:
        self.calls.append((ttn, phone))
        return self.parcel


class FakeCatalog:
    async def search(self, query: str, limit: int = 5) -> list[Any]:
        return []


class FakeTelegram:
    configured = True

    def __init__(self) -> None:
        self.notifications: list[dict[str, Any]] = []
        self.relayed: list[str] = []

    async def notify_handoff(self, conv: Any, **kwargs: Any) -> int | None:
        self.notifications.append(kwargs)
        return 4242

    async def relay_client_message(self, conv: Any, text: str) -> None:
        self.relayed.append(text)


def sample_order(**overrides: Any) -> OrderSummary:
    base: dict[str, Any] = {
        "id": 4521,
        "number": "4521",
        "status": "Відправлено",
        "created_at": "2026-10-20 10:00:00",
        "total": 2490.0,
        "payment_status": "paid",
        "buyer_name": "Іван Петренко",
        "products": ["Зарядний кабель Type 2"],
        "tracking_code": "20450000000001",
        "delivery_service": "Нова Пошта",
        "city": "Одеса",
        "receive_point": "Відділення №12",
        "last_history": None,
    }
    base.update(overrides)
    return OrderSummary(**base)
