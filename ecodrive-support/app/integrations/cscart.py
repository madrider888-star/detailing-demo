"""Каталог сайта (CS-Cart): поиск товаров через REST API или по странице поиска."""

from __future__ import annotations

import html
import re
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urljoin

import httpx

_ITEM_SPLIT_RE = re.compile(r'class="[^"]*\but2-gl__item\b|class="[^"]*\bty-grid-list__item\b')
_TITLE_LINK_RE = re.compile(r"<a\b([^>]*\bproduct-title\b[^>]*)>(.*?)</a>", re.S)
_HREF_RE = re.compile(r'href="([^"]+)"')
_PRICE_RE = re.compile(r'class="ty-price-num"[^>]*>([^<]+)<')
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_INVISIBLE_RE = re.compile("[​‌‍⁠﻿]")  # сайт вставляет их в цены


@dataclass
class Product:
    name: str
    url: str
    price: str | None
    in_stock: bool | None
    sku: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean(text: str) -> str:
    text = _INVISIBLE_RE.sub("", html.unescape(_TAG_RE.sub("", text)))
    return _WS_RE.sub(" ", text).strip()


def parse_search_html(page: str, base_url: str, limit: int = 5) -> list[Product]:
    """Товары со страницы поиска UniTheme2: имя и ссылка из .product-title, цена — .ty-price-num."""
    products: list[Product] = []
    chunks = _ITEM_SPLIT_RE.split(page)[1:]  # до первого товара — шапка страницы
    for chunk in chunks:
        link = _TITLE_LINK_RE.search(chunk)
        if link is None:
            continue
        href = _HREF_RE.search(link.group(1))
        name = _clean(link.group(2))
        if not name or href is None:
            continue
        price = _PRICE_RE.search(chunk)
        in_stock: bool | None = None
        if "ty-qty-out-of-stock" in chunk:
            in_stock = False
        elif "ty-qty-in-stock" in chunk:
            in_stock = True
        products.append(
            Product(
                name=name,
                url=urljoin(base_url, html.unescape(href.group(1))),
                price=_clean(price.group(1)) + " грн" if price else None,
                in_stock=in_stock,
            )
        )
        if len(products) >= limit:
            break
    return products


class CatalogClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_email: str = "",
        api_key: str = "",
        timeout: float = 15.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._api_email = api_email
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "EcodriveSupportBot/0.1 (+https://ecodrive.in.ua)"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def search(self, query: str, limit: int = 5) -> list[Product]:
        query = query.strip()
        if not query:
            return []
        if self._api_email and self._api_key:
            return await self._search_api(query, limit)
        return await self._search_html(query, limit)

    async def _search_api(self, query: str, limit: int) -> list[Product]:
        response = await self._client.get(
            f"{self._base}/api/2.0/products",
            params={"q": query, "items_per_page": str(limit), "status": "A"},
            auth=(self._api_email, self._api_key),
        )
        response.raise_for_status()
        items = response.json().get("products") or []
        products: list[Product] = []
        for item in items:
            if not isinstance(item, dict) or not item.get("product"):
                continue
            amount = item.get("amount")
            price = item.get("price")
            products.append(
                Product(
                    name=_clean(str(item["product"])),
                    url=f"{self._base}/index.php?dispatch=products.view&product_id={item.get('product_id')}",
                    price=f"{float(price):,.0f} грн".replace(",", " ") if price else None,
                    in_stock=(int(amount) > 0) if amount is not None else None,
                    sku=item.get("product_code") or None,
                )
            )
        return products[:limit]

    async def _search_html(self, query: str, limit: int) -> list[Product]:
        # Те же параметры, что отправляет форма поиска на сайте; без них CS-Cart отдаёт 404
        params = {
            "dispatch": "products.search",
            "q": query,
            "match": "all",
            "subcats": "Y",
            "pcode_from_q": "Y",
            "pshort": "Y",
            "pfull": "Y",
            "pname": "Y",
            "pkeywords": "Y",
            "search_performed": "Y",
        }
        response = await self._client.get(f"{self._base}/ru/", params=params)
        response.raise_for_status()
        return parse_search_html(response.text, self._base, limit)
