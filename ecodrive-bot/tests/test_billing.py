"""Шкала баланса OpenAI: расходы из Costs API минус записанная сумма."""

from __future__ import annotations

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import User
from app.services.openai_billing import (
    BillingError,
    BillingService,
    OpenAICostsClient,
    progress_bar,
)


def _costs(*values: float, next_page: str | None = None) -> httpx.Response:
    buckets = [
        {
            "object": "bucket",
            "start_time": 1730419200 + i * 86400,
            "end_time": 1730505600 + i * 86400,
            "results": [{"object": "organization.costs.result", "amount": {"value": v}}],
        }
        for i, v in enumerate(values)
    ]
    return httpx.Response(
        200,
        json={
            "object": "page",
            "data": buckets,
            "has_more": next_page is not None,
            "next_page": next_page,
        },
    )


async def test_costs_client_sums_all_pages() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if "page" not in request.url.params:
            return _costs(1.5, 2.25, next_page="p2")
        return _costs(0.25)

    client = OpenAICostsClient("sk-admin-test", transport=httpx.MockTransport(handler))
    assert await client.spent_since(1730419200) == pytest.approx(4.0)
    await client.aclose()
    assert seen[0].headers["authorization"] == "Bearer sk-admin-test"
    assert seen[0].url.path.endswith("/organization/costs")
    assert seen[0].url.params["start_time"] == "1730419200"
    assert seen[1].url.params["page"] == "p2"


async def test_costs_client_rejects_wrong_key() -> None:
    transport = httpx.MockTransport(lambda r: httpx.Response(401, json={}))
    client = OpenAICostsClient("sk-wrong", transport=transport)
    with pytest.raises(BillingError, match="Ключ администратора"):
        await client.spent_since(0)
    await client.aclose()


def test_progress_bar() -> None:
    assert progress_bar(1.0) == "🟩" * 10
    assert progress_bar(0.5) == "🟩" * 5 + "⬜" * 5
    assert progress_bar(0.15).startswith("🟨")
    assert progress_bar(0.01) == "🟥" + "⬜" * 9
    assert progress_bar(-0.2) == "⬜" * 10


async def test_balance_report_subtracts_spend_since_recorded(
    settings: Settings, session: AsyncSession, admin: User
) -> None:
    # Записали 100 $, когда за сутки было уже потрачено 1 $; сейчас OpenAI насчитал 31 $.
    spend = iter([1.0, 31.0])
    transport = httpx.MockTransport(lambda r: _costs(next(spend)))
    settings = settings.model_copy(update={"openai_admin_key": SecretStr("sk-admin-test")})
    service = BillingService(session, settings, transport=transport)
    assert "Сначала укажите" in await service.report()

    await service.set_balance(admin, 100.0)
    await session.commit()
    report = await service.report()
    assert "$70.00</b> из $100.00" in report
    assert "70%" in report
    assert "🟩" * 7 + "⬜" * 3 in report
    assert "Денег мало" not in report


async def test_low_balance_warns(settings: Settings, session: AsyncSession, admin: User) -> None:
    spend = iter([0.0, 95.0])
    transport = httpx.MockTransport(lambda r: _costs(next(spend)))
    settings = settings.model_copy(update={"openai_admin_key": SecretStr("sk-admin-test")})
    service = BillingService(session, settings, transport=transport)
    await service.set_balance(admin, 100.0)
    report = await service.report()
    assert "Денег мало" in report
    assert "platform.openai.com" in report
