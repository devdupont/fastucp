import logging
from typing import Any

log = logging.getLogger(__name__)


class InMemoryStore:
    """
    Simple, memory-based data store.
    In a real application, this would be a Redis or PostgreSQL connection.
    """

    def __init__(self) -> None:
        self._products: dict[str, dict[str, Any]] = {}
        self._sessions: dict[str, Any] = {}
        self._orders: dict[str, Any] = {}

    # --- PRODUCT MANAGEMENT ---
    def add_product(self, sku: str, title: str, price: int, img: str, desc: str = "") -> None:
        self._products[sku] = {"title": title, "price": price, "image": img, "desc": desc}

    def get_product(self, sku: str) -> dict[str, Any] | None:
        return self._products.get(sku)

    def list_products(self) -> dict[str, dict[str, Any]]:
        return self._products

    def save_session(self, session_id: str, cart_data: Any) -> None:
        """Saves the CheckoutResponse object or its dict representation."""
        self._sessions[session_id] = cart_data
        log.info("💾 STORE: Cart Saved -> %s", session_id)

    def get_session(self, session_id: str) -> Any | None:
        return self._sessions.get(session_id)

    def create_order(self, order_id: str, order_data: Any) -> None:
        self._orders[order_id] = order_data
        log.info("💾 STORE: Order Created -> %s", order_id)

    def get_order(self, order_id: str) -> Any | None:
        return self._orders.get(order_id)
