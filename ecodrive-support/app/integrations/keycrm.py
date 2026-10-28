"""KeyCRM: заказы клиента по телефону и заявки менеджерам (карточки в воронке)."""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import httpx

from app.core.logging import get_logger

log = get_logger(__name__)


def normalize_phone(raw: str) -> str | None:
    """Телефон в международном формате с плюсом: 067… → +38067…"""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 10 and digits.startswith("0"):
        digits = "38" + digits
    if len(digits) == 12 and digits.startswith("380"):
        return "+" + digits
    if 10 <= len(digits) <= 15:
        return "+" + digits  # иностранный номер
    return None


def _get(data: Any, *path: str) -> Any:
    for key in path:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


@dataclass
class OrderSummary:
    id: int
    number: str
    status: str | None
    created_at: str | None
    total: float | None
    payment_status: str | None
    buyer_name: str | None
    products: list[str] = field(default_factory=list)
    tracking_code: str | None = None
    delivery_service: str | None = None
    city: str | None = None
    receive_point: str | None = None
    last_history: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_order(raw: dict[str, Any]) -> OrderSummary:
    """Терпимый разбор заказа из `GET /order?include=…` — поля в CRM могут отсутствовать."""
    products: list[str] = []
    for item in raw.get("products") or []:
        name = item.get("name") or _get(item, "offer", "name") or "товар"
        qty = item.get("quantity")
        products.append(f"{name} × {qty:g}" if isinstance(qty, int | float) and qty != 1 else name)

    shipping = raw.get("shipping") or {}
    service = _get(shipping, "delivery_service", "name") or _get(
        shipping, "deliveryService", "name"
    )
    if service is None and isinstance(shipping.get("delivery_service"), str):
        service = shipping["delivery_service"]

    last = shipping.get("last_history") or shipping.get("lastHistory") or {}
    last_text = None
    if isinstance(last, dict):
        parts = [last.get("status"), last.get("created_at") or last.get("date")]
        last_text = " — ".join(str(p) for p in parts if p) or None

    total = raw.get("grand_total")
    return OrderSummary(
        id=int(raw["id"]),
        number=str(raw.get("source_uuid") or raw["id"]),
        status=_get(raw, "status", "name") or raw.get("status_name"),
        created_at=raw.get("created_at"),
        total=float(total) if isinstance(total, int | float | str) and str(total) else None,
        payment_status=raw.get("payment_status"),
        buyer_name=_get(raw, "buyer", "full_name"),
        products=products,
        tracking_code=shipping.get("tracking_code") or None,
        delivery_service=service,
        city=shipping.get("shipping_address_city") or None,
        receive_point=shipping.get("shipping_receive_point") or None,
        last_history=last_text,
    )


class KeyCRMClient:
    INCLUDE = "buyer,status,products,shipping.lastHistory,shipping.deliveryService"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://openapi.keycrm.app/v1",
        pipeline_id: int | None = None,
        source_id: int | None = None,
        timeout: float = 15.0,
        cache_ttl: float = 120.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base = base_url.rstrip("/")
        self._pipeline_id = pipeline_id
        self._source_id = source_id
        self._client = client or httpx.AsyncClient(timeout=timeout)
        # Лимит KeyCRM — 20 запросов в минуту на ключ: запросы по очереди и кэш по телефону
        self._lock = asyncio.Lock()
        self._cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, list[OrderSummary]]] = {}

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    async def close(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"}

    async def find_orders_by_phone(self, phone: str, limit: int = 5) -> list[OrderSummary]:
        """Последние заказы покупателя с этим телефоном (новые первыми)."""
        normalized = normalize_phone(phone)
        if normalized is None or not self.configured:
            return []
        cached = self._cache.get(normalized)
        if cached and time.monotonic() - cached[0] < self._cache_ttl:
            return cached[1]
        async with self._lock:
            orders = await self._fetch_orders(normalized, limit)
            if not orders and normalized.startswith("+380"):
                # В CRM номер мог быть сохранён в локальном формате 0XX…
                orders = await self._fetch_orders("0" + normalized[4:], limit)
        self._cache[normalized] = (time.monotonic(), orders)
        return orders

    async def _fetch_orders(self, phone: str, limit: int) -> list[OrderSummary]:
        params = {
            "filter[buyer_phone]": phone,
            "include": self.INCLUDE,
            "sort": "-id",
            "limit": str(limit),
        }
        response = await self._client.get(
            f"{self._base}/order", params=params, headers=self._headers()
        )
        response.raise_for_status()
        data = response.json().get("data") or []
        return [parse_order(item) for item in data if isinstance(item, dict) and "id" in item]

    async def create_lead(
        self, *, title: str, phone: str | None, full_name: str | None, comment: str
    ) -> int | None:
        """Карточка в воронке KeyCRM для менеджеров; None — CRM не настроена или отказала."""
        if not self.configured:
            return None
        payload: dict[str, Any] = {
            "title": title,
            "manager_comment": comment,
            "contact": {"full_name": full_name or "Клиент с сайта", "phone": phone},
        }
        if self._pipeline_id is not None:
            payload["pipeline_id"] = self._pipeline_id
        if self._source_id is not None:
            payload["source_id"] = self._source_id
        async with self._lock:
            response = await self._client.post(
                f"{self._base}/pipelines/cards", json=payload, headers=self._headers()
            )
        if response.status_code >= 400:
            log.warning("keycrm.lead_failed", status=response.status_code, body=response.text[:300])
            return None
        card_id = response.json().get("id")
        return int(card_id) if card_id is not None else None
