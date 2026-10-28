from __future__ import annotations

from app.integrations.cscart import parse_search_html

PAGE = """
<div class="header">...</div>
<div class="ty-grid-list__item ut2-gl__item">
  <div class="ut2-gl__name"><a href="/ru/kugoo-g4/" class="product-title" title="G4">
    Электросамокат Kugoo Kirin G4 2026</a></div>
  <span class="ty-price-num">&#8205;39&nbsp;990&#8205;</span>
  <span class="ty-qty-in-stock">В наличии</span>
</div>
<div class="ty-grid-list__item ut2-gl__item">
  <div class="ut2-gl__name">
    <a class="product-title" href="https://ecodrive.in.ua/ru/kugoo-g2/">Kugoo G2</a></div>
  <span class="ty-qty-out-of-stock">Нет в наличии</span>
</div>
"""


def test_parse_search_html_extracts_name_price_stock_and_links() -> None:
    products = parse_search_html(PAGE, "https://ecodrive.in.ua")
    assert [p.name for p in products] == ["Электросамокат Kugoo Kirin G4 2026", "Kugoo G2"]
    assert products[0].url == "https://ecodrive.in.ua/ru/kugoo-g4/"
    assert products[0].price == "39 990 грн"
    assert products[0].in_stock is True
    assert products[1].price is None
    assert products[1].in_stock is False
