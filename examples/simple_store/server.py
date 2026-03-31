"""A simple FastUCP server simulating a tech store checkout flow. This example demonstrates the discovery, checkout creation, update, and completion phases of the UCP protocol."""

# ruff: noqa: INP001, T201, BLE001

import logging
import uuid
from typing import Any

import uvicorn
from ucp_sdk.models.schemas.shopping.types.order_line_item import OrderLineItem, Quantity

from fastucp import CheckoutBuilder, FastUCP
from fastucp.exceptions import UCPError
from fastucp.presets import Capability
from fastucp.types import (
    CheckoutCreateRequest,
    CheckoutResponse,
    CheckoutUpdateRequest,
    Fulfillment,
    HttpsUrl,
    Order,
    ResponseOrder,
)

logging.basicConfig(level=logging.INFO)


app = FastUCP(title="FastUCP Tech Store", base_url="http://127.0.0.1:8000", enable_mcp=True, version="2026-01-11")

# --- SIMPLE DATABASE SIMULATION ---
SESSIONS: dict[str, CheckoutResponse] = {}

PRODUCTS = {
    "sku_pixel": {
        "id": "sku_pixel",
        "title": "Google Pixel 9 Pro",
        "description": "The latest AI-powered smartphone from Google.",
        "price": 99900,  # $999.00
        "image_url": "https://store.google.com/pixel.jpg",
        "weight": 0.5,
    },
    "sku_case": {
        "id": "sku_case",
        "title": "Pixel 9 Case - Charcoal",
        "description": "Durable fabric case for Pixel 9.",
        "price": 2900,  # $29.00
        "image_url": "https://store.google.com/case.jpg",
        "weight": 0.1,
    },
    "sku_buds": {
        "id": "sku_buds",
        "title": "Pixel Buds Pro 2",
        "description": "Noise cancelling wireless earbuds.",
        "price": 19900,  # $199.00
        "image_url": "https://store.google.com/buds.jpg",
        "weight": 0.2,
    },
}


# --- 1. Discovery ---
@app.discovery
def search_products(query: str = ""):
    """Search products."""
    print(f"🔎 Server: Searching for '{query}'...")
    results = [
        {"id": item["id"], "title": item["title"], "price": item["price"], "image_url": item["image_url"]}
        for item in PRODUCTS.values()
        if query.lower() in item["title"].lower()
    ]
    return {"items": results}


# --- 2. Create Checkout ---
@app.checkout
def create_session(payload: CheckoutCreateRequest) -> CheckoutResponse:
    # Generate a new Session ID
    session_id = str(uuid.uuid4())

    builder = CheckoutBuilder(app, session_id=session_id)

    # Mandatory Links
    builder.links = [
        {"type": "privacy_policy", "url": "https://example.com/privacy"},
        {"type": "terms_of_service", "url": "https://example.com/terms"},
    ]

    # Add items
    for req_item in payload.line_items:
        product = PRODUCTS.get(req_item.item.id)
        if product:
            builder.add_item(
                item_id=product["id"],
                title=product["title"],
                price=product["price"],
                quantity=req_item.quantity,
                img_url=product["image_url"],
            )

    if payload.buyer:
        builder.set_buyer(payload.buyer)

    response = builder.build()

    # Save Session (Needed during Complete phase)
    SESSIONS[session_id] = response
    print(f"💾 Session Created: {session_id}")

    return response


# --- 3. Update Checkout ---
@app.update_checkout
def update_session(session_id: str, payload: CheckoutUpdateRequest) -> CheckoutResponse:
    # We could retrieve old session data, but here we rebuild it using the Builder pattern.
    # In a real scenario, fetch the current state from SESSIONS[session_id] and pass it to the builder.
    builder = CheckoutBuilder(app, session_id=session_id)

    product = PRODUCTS["sku_pixel"]
    builder.add_item(product["id"], product["title"], product["price"], 1, product["image_url"])

    builder.links = [
        {"type": "privacy_policy", "url": "https://example.com/privacy"},
        {"type": "terms_of_service", "url": "https://example.com/terms"},
    ]

    builder.set_buyer(payload.buyer)

    # Shipping Logic
    if payload.buyer and payload.buyer.email:
        builder.add_shipping_option("ship_std", "Standard Shipping", 500, "5-7 Days")
        builder.select_shipping_option("ship_std")
    else:
        builder.add_error("missing", "$.buyer.email", "Email required for shipping.")

    response = builder.build()
    SESSIONS[session_id] = response  # Save updated state
    return response


@app.complete_checkout
def complete_session(session_id: str, payment: dict[str, Any]) -> Order:
    """
    Finalizes the order and returns an Order object.
    """
    print(f"💰 Payment Received: {payment}")

    # 1. Session Check
    checkout_session = SESSIONS.get(session_id)
    if not checkout_session:
        # Error can be raised (using UCPError)
        raise UCPError(code="not_found", message="Checkout session not found.", path="$.id", status_code=404)

    # 2. Payment Verification (Mock)
    # In real life, verify 'payment' token with Stripe/Iyzico/etc.
    if not payment.get("token"):
        pass

    order_line_items = [
        OrderLineItem(
            id=li.id,
            item=li.item,
            quantity=Quantity(total=li.quantity, fulfilled=0),
            totals=li.totals,
            status="processing",
        )
        for li in checkout_session.line_items
    ]

    # 4. Create Order Object
    order_id = f"ord_{uuid.uuid4().hex[:8]}"

    # Creating UCP Context (Capabilities)
    ucp_context = ResponseOrder(
        version=app.ucp_version,
        capabilities=[
            # Which capabilities are active post-order
            Capability.ORDER.value.as_response(),
        ],
    )

    order = Order(
        ucp=ucp_context,
        id=order_id,
        checkout_id=session_id,
        permalink_url=HttpsUrl(f"https://example.com/orders/{order_id}"),
        line_items=order_line_items,
        totals=checkout_session.totals,
        fulfillment=Fulfillment(
            expectations=[],  # Fulfillment expectations can be added here
            events=[],
        ),
    )

    print(f"🎉 Order Created: {order_id}")
    return order


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
