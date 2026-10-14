"""Остаток денег на счёте OpenAI — шкала в боте.

У OpenAI нет API «покажи баланс»: есть только расходы по дням
(`GET /organization/costs`, нужен ключ администратора). Поэтому администратор
после пополнения пишет боту, сколько сейчас на счёте (`/balance 100`), а бот
вычитает из этой суммы расходы, которые OpenAI насчитал с того момента.

Расходы считаются от начала суток (UTC) записи, минус то, что уже было потрачено
в эти сутки к моменту записи (`baseline`): так результат верен, как бы OpenAI ни
выравнивал дневные корзины.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.models import AuditLog, User
from app.repositories.audit import AuditRepository

log = get_logger(__name__)

BALANCE_ACTION = "billing.balance_set"
BILLING_URL = "https://platform.openai.com/settings/organization/billing/overview"
BAR_CELLS = 10
MAX_PAGES = 20


class BillingError(Exception):
    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message


@dataclass(frozen=True)
class BalanceSnapshot:
    amount: float  # сколько было на счёте в момент записи, $
    day_start: int  # начало суток записи (UTC), unix
    baseline: float  # потрачено в эти сутки до записи, $
    set_at: datetime


def day_start_utc(moment: datetime) -> int:
    midnight = moment.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight.timestamp())


class OpenAICostsClient:
    """Сумма расходов организации из Costs API (ключ администратора, только чтение)."""

    def __init__(
        self,
        admin_key: str,
        base_url: str = "https://api.openai.com/v1",
        *,
        timeout: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {admin_key}"},
            timeout=timeout,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def spent_since(self, start_time: int) -> float:
        total = 0.0
        params: dict[str, str | int] = {
            "start_time": start_time,
            "bucket_width": "1d",
            "limit": 180,
        }
        for _ in range(MAX_PAGES):
            try:
                response = await self._client.get("/organization/costs", params=params)
            except httpx.HTTPError as exc:
                raise BillingError("OpenAI не ответил. Попробуйте позже.") from exc
            if response.status_code == 401:
                raise BillingError(
                    "OpenAI не принял ключ администратора (OPENAI_ADMIN_KEY). Нужен именно "
                    "Admin key — он начинается с sk-admin-, обычный ключ sk-proj- не подойдёт."
                    + _openai_reason(response)
                )
            if response.status_code == 403:
                raise BillingError(
                    "У ключа администратора нет доступа к расходам. Создайте Admin key "
                    "под владельцем организации (Owner), права — Read only или All."
                    + _openai_reason(response)
                )
            if response.status_code >= 400:
                log.warning("billing.costs_error", status=response.status_code)
                raise BillingError(
                    f"OpenAI не отдал расходы (код {response.status_code}). Попробуйте позже."
                )
            try:
                payload = response.json()
                for bucket in payload.get("data") or []:
                    for result in bucket.get("results") or []:
                        total += float(str((result.get("amount") or {}).get("value", 0)))
            except (ValueError, TypeError, AttributeError) as exc:
                raise BillingError("OpenAI вернул непонятный ответ о расходах.") from exc
            next_page = payload.get("next_page")
            if not payload.get("has_more") or not next_page:
                break
            params["page"] = str(next_page)
        return total


def _openai_reason(response: httpx.Response) -> str:
    """Текст ошибки от OpenAI (ключ в нём замаскирован) — чтобы было видно точную причину."""
    try:
        message = str((response.json().get("error") or {}).get("message") or "")
    except (ValueError, AttributeError):
        message = ""
    return f"\n\nOpenAI: {message[:300]}" if message else ""


def progress_bar(fraction: float) -> str:
    fraction = min(max(fraction, 0.0), 1.0)
    filled = round(fraction * BAR_CELLS)
    if fraction > 0 and filled == 0:
        filled = 1
    cell = "🟩" if fraction >= 0.3 else "🟨" if fraction >= 0.1 else "🟥"
    return cell * filled + "⬜" * (BAR_CELLS - filled)


def render_report(snapshot: BalanceSnapshot, spent: float, low_usd: float) -> str:
    remaining = snapshot.amount - spent
    fraction = remaining / snapshot.amount if snapshot.amount > 0 else 0.0
    lines = [
        "💰 <b>Баланс OpenAI</b> (примерно)",
        "",
        f"{progress_bar(fraction)} {max(fraction, 0.0) * 100:.0f}%",
        f"Осталось: <b>${max(remaining, 0.0):.2f}</b> из ${snapshot.amount:.2f}",
        f"Потрачено с {snapshot.set_at.astimezone(UTC):%d.%m %H:%M} UTC: ${spent:.2f}",
    ]
    if remaining <= low_usd:
        lines += ["", f"⚠️ Денег мало — пополните счёт:\n{BILLING_URL}"]
    lines += [
        "",
        "<i>OpenAI сообщает расходы с задержкой до нескольких часов.</i>",
        "После пополнения напишите, сколько стало на счёте: <code>/balance 100</code>",
    ]
    return "\n".join(lines)


class BillingService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.transport = transport

    @property
    def has_admin_key(self) -> bool:
        return bool(self.settings.openai_admin_key.get_secret_value())

    async def _spent(self, start_time: int) -> float:
        client = OpenAICostsClient(
            self.settings.openai_admin_key.get_secret_value(),
            self.settings.openai_base_url,
            transport=self.transport,
        )
        try:
            return await client.spent_since(start_time)
        finally:
            await client.aclose()

    async def latest_snapshot(self) -> BalanceSnapshot | None:
        entry = await self.session.scalar(
            select(AuditLog)
            .where(AuditLog.action == BALANCE_ACTION)
            .order_by(AuditLog.id.desc())
            .limit(1)
        )
        if entry is None:
            return None
        meta = entry.metadata_
        return BalanceSnapshot(
            amount=float(meta["amount"]),
            day_start=int(meta["day_start"]),
            baseline=float(meta.get("baseline", 0.0)),
            set_at=datetime.fromisoformat(meta["set_at"]),
        )

    async def set_balance(self, actor: User, amount: float) -> BalanceSnapshot:
        now = datetime.now(UTC)
        day_start = day_start_utc(now)
        baseline = 0.0
        if self.has_admin_key:
            try:
                baseline = await self._spent(day_start)
            except BillingError:
                log.warning("billing.baseline_unavailable")
        await AuditRepository(self.session).log(
            BALANCE_ACTION,
            user_id=actor.id,
            amount=amount,
            day_start=day_start,
            baseline=baseline,
            set_at=now.isoformat(),
        )
        return BalanceSnapshot(amount, day_start, baseline, now)

    async def report(self) -> str:
        snapshot = await self.latest_snapshot()
        if snapshot is None:
            return (
                "💰 <b>Баланс OpenAI</b>\n\n"
                f"Сначала укажите, сколько сейчас на счёте. Откройте\n{BILLING_URL}\n"
                "и напишите сумму из строки <b>Credit balance</b>, например: "
                "<code>/balance 100</code>"
            )
        if not self.has_admin_key:
            return (
                f"💰 <b>Баланс OpenAI</b>\n\nЗаписано: ${snapshot.amount:.2f} "
                f"({snapshot.set_at.astimezone(UTC):%d.%m %H:%M} UTC).\n\n"
                "Чтобы бот видел расходы, на сервере нужен ключ администратора OpenAI "
                "(<code>OPENAI_ADMIN_KEY</code>)."
            )
        spent = max(0.0, await self._spent(snapshot.day_start) - snapshot.baseline)
        return render_report(snapshot, spent, self.settings.openai_balance_low_usd)
