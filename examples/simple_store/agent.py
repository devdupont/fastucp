"""Happy path for an agent simulation using the FastUCPClient to interact with the server."""

# ruff: noqa: INP001, T201, BLE001

import json
import time

from fastucp import FastUCPClient


def print_json(label, data):
    """Helper to pretty print JSON for debugging."""
    print(f"\n--- {label} ---")
    print(json.dumps(data, indent=2))
    print("-" * (len(label) + 8) + "\n")


def run_agent_simulation():
    # 1. Initialize Client using MCP Transport
    # We use 'mcp' to see the JSON-RPC wrapping
    client = FastUCPClient(base_url="http://127.0.0.1:8000", transport="mcp")

    print("\n🤖 === STEP 1: Discovery (Searching for 'Pixel') ===")

    try:
        # FIX: We must wrap the call in "tools/call" structure for MCP
        mcp_response = client._send_mcp(  # noqa: SLF001
            "tools/call",
            {
                "name": "search_products",
                "arguments": {"query": "Pixel"},
            },
        )

        # FIX: Extract the actual data.
        # The server returns {_raw: {...}, content: [...]}
        if "_raw" in mcp_response:
            search_results = mcp_response["_raw"]
        else:
            # Fallback: Parse the string content if _raw is missing
            search_results = json.loads(mcp_response["content"][0]["text"])

        print_json("Search Results", search_results)

        items = search_results.get("items", [])
        if not items:
            print("No items found. Exiting.")
            return

        selected_item = items[0]
        print(f"✅ Selected: {selected_item['title']} (${selected_item['price']/100})")

    except Exception as e:
        print(f"❌ Search failed: {e}")
        return

    print("\n🤖 === STEP 2: Create Checkout Session ===")
    line_items = [{"item": {"id": selected_item["id"]}, "quantity": 1}]

    # This uses the SDK method (ensure fastucp/client.py is updated to use tools/call)
    checkout_session = client.create_checkout(line_items=line_items)
    session_id = checkout_session.id

    print_json("Checkout Created (Response)", checkout_session.model_dump(mode="json", exclude_none=True))
    print(f"✅ Session ID: {session_id}")

    # Simulate user thinking time
    time.sleep(1)

    print("\n🤖 === STEP 3: Update Buyer Info (Trigger Shipping Calc) ===")
    buyer_info = {"email": "agent@example.com", "first_name": "Agent", "last_name": "Smith"}

    # Send update request
    updated_session = client.update_checkout(session_id, buyer_data=buyer_info)

    # Inspect the JSON to see Shipping Options returned by the builder
    dump = updated_session.model_dump(mode="json", exclude_none=True)
    print_json("Updated Session (With Shipping)", dump)

    # Extract shipping options safely
    fulfillment = dump.get("fulfillment", {})
    methods = fulfillment.get("methods", [])

    shipping_opts = []
    if methods:
        groups = methods[0].get("groups", [])
        if groups:
            shipping_opts = groups[0].get("options", [])

    if shipping_opts:
        print(f"✅ Found {len(shipping_opts)} shipping options.")
        print(f"   Option 1: {shipping_opts[0]['title']} - ${shipping_opts[0]['totals'][0]['amount']/100}")

    print("\n🤖 === STEP 4: Complete Order ===")
    # Fake payment token
    payment_data = {"token": "tok_visa_fake", "type": "tokenized_card"}

    order = client.complete_checkout(session_id, payment_data)
    print_json("Order Confirmation", order.model_dump(mode="json", exclude_none=True))
    print("🎉 Purchase Complete!")


if __name__ == "__main__":
    # Ensure server is running first!
    try:
        run_agent_simulation()
    except Exception as e:
        print(f"❌ Connection Error: Ensure server.py is running on port 8000. \nDetail: {e}")
