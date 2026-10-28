from __future__ import annotations

import httpx

from app.integrations.keycrm import KeyCRMClient, normalize_phone, parse_order


def test_normalize_phone_local_to_international() -> None:
    assert normalize_phone("097 342 34 55") == "+380973423455"
    assert normalize_phone("+38 (097) 342-34-55") == "+380973423455"
    assert normalize_phone("12") is None


def test_parse_order_tolerates_missing_fields() -> None:
    raw = {
        "id": 4521,
        "source_uuid": "W-4521",
        "grand_total": "2490.00",
        "payment_status": "paid",
        "status": {"name": "Відправлено"},
        "buyer": {"full_name": "Іван"},
        "products": [{"name": "Кабель", "quantity": 2}, {"offer": {"name": "Перехідник"}}],
        "shipping": {
            "tracking_code": "20450000000001",
            "shipping_address_city": "Одеса",
            "delivery_service": {"name": "Нова Пошта"},
            "lastHistory": {"status": "В дорозі", "created_at": "2026-10-21"},
        },
    }
    order = parse_order(raw)
    assert order.number == "W-4521"
    assert order.total == 2490.0
    assert order.products == ["Кабель × 2", "Перехідник"]
    assert order.tracking_code == "20450000000001"
    assert order.delivery_service == "Нова Пошта"
    assert order.last_history == "В дорозі — 2026-10-21"


async def test_find_orders_retries_local_phone_format_and_caches() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        phone = request.url.params["filter[buyer_phone]"]
        seen.append(phone)
        data = [{"id": 1}] if phone.startswith("0") else []
        return httpx.Response(200, json={"data": data})

    client = KeyCRMClient("key", client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    orders = await client.find_orders_by_phone("097 342 34 55")
    assert [o.id for o in orders] == [1]
    assert seen == ["+380973423455", "0973423455"]
    await client.find_orders_by_phone("+380973423455")
    assert len(seen) == 2  # второй раз — из кэша
