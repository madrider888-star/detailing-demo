"""Нова Пошта: статус посылки по номеру накладной (ТТН). Ключ API не обязателен."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any

import httpx

API_URL = "https://api.novaposhta.ua/v2.0/json/"

# Коды статусов НП → понятное описание. Полный список: developers.novaposhta.ua
STATUS_TEXT: dict[str, str] = {
    "1": "Накладна створена, але відправник ще не передав посилку у відділення",
    "2": "Накладну видалено",
    "3": "Номер накладної не знайдено",
    "4": "Посилка у місті відправника",
    "41": "Посилка у місті відправника (місцева доставка)",
    "5": "Посилка прямує до міста отримувача",
    "6": "Посилка у місті отримувача, скоро буде у відділенні",
    "7": "Посилка прибула у відділення, можна забирати",
    "8": "Посилка прибула у поштомат, можна забирати",
    "9": "Посилку отримано",
    "10": "Посилку отримано, грошовий переказ видано",
    "11": "Посилку отримано, грошовий переказ видано",
    "12": "Посилка комплектується",
    "14": "Посилку передано на доставку",
    "101": "Посилка прямує до отримувача (курʼєр)",
    "102": "Відмова від отримання",
    "103": "Відмова від отримання (адресна доставка)",
    "104": "Змінено адресу доставки",
    "105": "Зберігання припинено",
    "106": "Посилку отримано, створено зворотну накладну",
    "111": "Невдала спроба доставки",
    "112": "Дата доставки перенесена отримувачем",
}
IN_TRANSIT = frozenset({"4", "41", "5", "6", "12", "14", "101"})
READY_FOR_PICKUP = frozenset({"7", "8"})
DELIVERED = frozenset({"9", "10", "11", "106"})

_DATE_FORMATS = (
    "%d.%m.%Y %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%d.%m.%Y",
    "%Y-%m-%d",
)


@dataclass
class ParcelStatus:
    number: str
    status_code: str
    status: str  # текст статуса от НП
    stage: str  # created | in_transit | ready_for_pickup | delivered | problem | unknown
    recipient_city: str | None
    recipient_warehouse: str | None
    scheduled_delivery: str | None
    actual_delivery: str | None
    created: str | None
    sender_city: str | None
    delayed: bool  # обещанная дата прошла, а посылка ещё в пути
    days_in_transit: int | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_ttn(raw: str) -> str | None:
    """Номер накладной НП — 14 цифр; пробелы и дефисы допускаются."""
    digits = re.sub(r"\D", "", raw or "")
    return digits if len(digits) == 14 else None


def _parse_date(value: Any) -> date | None:
    if not value or not isinstance(value, str):
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _stage(code: str) -> str:
    if code in IN_TRANSIT:
        return "in_transit"
    if code in READY_FOR_PICKUP:
        return "ready_for_pickup"
    if code in DELIVERED:
        return "delivered"
    if code == "1":
        return "created"
    if code in {"2", "3"}:
        return "unknown"
    return "problem"


def summarize(doc: dict[str, Any], today: date | None = None) -> ParcelStatus:
    """Сводка по документу из ответа getStatusDocuments."""
    today = today or date.today()
    code = str(doc.get("StatusCode") or "")
    status = str(doc.get("Status") or STATUS_TEXT.get(code) or "Статус невідомий")
    scheduled = _parse_date(doc.get("ScheduledDeliveryDate"))
    created = _parse_date(doc.get("DateCreated"))
    stage = _stage(code)
    delayed = stage == "in_transit" and scheduled is not None and scheduled < today
    days = (today - created).days if created and stage == "in_transit" else None
    return ParcelStatus(
        number=str(doc.get("Number") or ""),
        status_code=code,
        status=status,
        stage=stage,
        recipient_city=doc.get("CityRecipient") or None,
        recipient_warehouse=doc.get("WarehouseRecipient") or None,
        scheduled_delivery=doc.get("ScheduledDeliveryDate") or None,
        actual_delivery=doc.get("ActualDeliveryDate") or doc.get("RecipientDateTime") or None,
        created=doc.get("DateCreated") or None,
        sender_city=doc.get("CitySender") or None,
        delayed=delayed,
        days_in_transit=days,
    )


class NovaPoshtaClient:
    def __init__(
        self,
        api_key: str = "",
        *,
        timeout: float = 15.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def track(self, ttn: str, phone: str | None = None) -> ParcelStatus | None:
        """Статус посылки; None — накладная не найдена или ответ пустой."""
        number = normalize_ttn(ttn)
        if number is None:
            raise ValueError("Номер накладної має містити 14 цифр")
        payload = {
            "apiKey": self._api_key,
            "modelName": "TrackingDocument",
            "calledMethod": "getStatusDocuments",
            "methodProperties": {
                "Documents": [{"DocumentNumber": number, "Phone": re.sub(r"\D", "", phone or "")}]
            },
        }
        response = await self._client.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        docs = data.get("data") or []
        if not docs:
            return None
        parcel = summarize(docs[0])
        return None if parcel.status_code == "3" else parcel
