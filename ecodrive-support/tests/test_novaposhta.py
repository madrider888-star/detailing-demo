from __future__ import annotations

from datetime import date

import httpx

from app.integrations.novaposhta import NovaPoshtaClient, normalize_ttn, summarize


def test_normalize_ttn_accepts_spaces_and_rejects_short() -> None:
    assert normalize_ttn("2045 0000 0000 01") == "20450000000001"
    assert normalize_ttn("204500") is None


def test_summarize_marks_delay_when_promised_date_passed() -> None:
    doc = {
        "Number": "20450000000001",
        "StatusCode": "5",
        "Status": "Прямує до міста отримувача",
        "ScheduledDeliveryDate": "20.10.2026 00:00:00",
        "DateCreated": "17.10.2026 12:30:00",
        "CityRecipient": "Одеса",
    }
    parcel = summarize(doc, today=date(2026, 10, 24))
    assert parcel.stage == "in_transit"
    assert parcel.delayed is True
    assert parcel.days_in_transit == 7


def test_summarize_ready_for_pickup_is_not_delayed() -> None:
    doc = {"StatusCode": "7", "ScheduledDeliveryDate": "20.10.2026 00:00:00"}
    parcel = summarize(doc, today=date(2026, 10, 24))
    assert parcel.stage == "ready_for_pickup"
    assert parcel.delayed is False
    assert "можна забирати" in parcel.status


async def test_track_returns_none_when_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": True, "data": [{"StatusCode": "3"}]})

    client = NovaPoshtaClient(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    assert await client.track("20450000000001") is None
