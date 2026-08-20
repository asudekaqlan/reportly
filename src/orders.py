"""Demo orders leftover. Not used on the ITSM path."""

from __future__ import annotations

from datetime import date, timedelta

RETURN_WINDOW_DAYS = 14


def _delivered(days_ago: int) -> str:
    return (date.today() - timedelta(days=days_ago)).isoformat()


def demo_orders() -> list[dict]:
    """Same catalog for every local customer. Dates stay relative to today."""
    return [
        {
            "id": "RLY-1042",
            "delivered_at": _delivered(5),
            "items": [
                {"id": "tee", "name": "Beyaz pamuklu tişört", "price": 249},
                {"id": "jeans", "name": "Lacivert kot pantolon", "price": 599},
                {"id": "socks", "name": "Pamuklu çorap 3'lü", "price": 89},
                {"id": "belt", "name": "Deri kemer", "price": 179},
            ],
        },
        {
            "id": "RLY-1098",
            "delivered_at": _delivered(2),
            "items": [
                {"id": "buds", "name": "Kablosuz kulaklık", "price": 890},
            ],
        },
        {
            "id": "RLY-0881",
            "delivered_at": _delivered(40),
            "items": [
                {"id": "maker", "name": "Filtre kahve makinesi", "price": 1299},
            ],
        },
    ]


def get_order(order_id: str) -> dict | None:
    for order in demo_orders():
        if order["id"] == order_id:
            return order
    return None


def order_total(order: dict) -> int:
    return sum(int(item["price"]) for item in order.get("items") or [])


def days_since_delivery(order: dict) -> int:
    delivered = date.fromisoformat(str(order["delivered_at"]))
    return (date.today() - delivered).days


def within_return_window(order: dict) -> bool:
    return days_since_delivery(order) <= RETURN_WINDOW_DAYS


def items_by_ids(order: dict, product_ids: list[str]) -> list[dict]:
    wanted = set(product_ids)
    return [item for item in order.get("items") or [] if item["id"] in wanted]


RETURN_REASONS = (
    "Beğenmedim",
    "Yanlış beden / numara",
    "Yanlış ürün geldi",
    "Vazgeçtim",
    "Diğer",
)
