import logging
import uuid
from json import JSONDecodeError
from typing import Any

from fastapi import Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from fastucp.protocols.protocol import Protocol

log = logging.getLogger(__name__)


class A2AProtocol(Protocol):
    """
    Handles Agent-to-Agent (A2A) Message Protocol.
    Compliant with UCP A2A Binding Specification (2026-01-11).
    """

    def handle_agent_card(self) -> dict:
        """
        /.well-known/agent-card.json
        """
        capabilities = []
        for name in self.app._handlers:  # noqa: SLF001
            # Naming according to Spec (dev.ucp.shopping...)
            cap_name = (
                "dev.ucp.shopping.checkout"
                if name == "create_checkout"
                else f"dev.ucp.shopping.{name.replace('create_session', 'checkout').replace('_checkout', '')}"
            )

            capabilities.append({"name": cap_name, "version": "2026-01-11"})

        return {
            "type": "agent-card",
            "extensions": [
                {
                    "uri": "https://ucp.dev/specification/reference?v=2026-01-11",
                    "description": "Business agent supporting UCP Checkout",
                    "params": {"capabilities": capabilities},
                }
            ],
        }

    async def handle_message(self, request: Request, _: str = Header(None, alias="UCP-Agent")) -> JSONResponse:
        """
        POST /agent/message
        Handles structured A2A messages conformant to UCP Spec.
        """
        try:
            body: dict[str, Any] = await request.json()
        except JSONDecodeError:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

        message_wrapper: dict[str, Any]
        try:
            message_wrapper = body["poarams"]["message"]
        except KeyError:
            message_wrapper = body.get("message", {})

        context_id = message_wrapper.get("contextId", str(uuid.uuid4()))
        parts: list[dict[str, Any]] = message_wrapper.get("parts", [])

        # --- PARSING LOGIC ---

        data_part = next((p for p in parts if p.get("type") == "data" or p.get("kind") == "data"), None)
        text_part = next((p for p in parts if p.get("type") == "text" or p.get("kind") == "text"), None)

        payload: dict[str, Any]
        action: str
        internal_method: str

        if data_part:
            # Structured Data (Button clicks, etc.)
            log.info("⚙️ Data Part Detected")
            payload = data_part.get("data", {})
            action = payload.get("action", "")
            internal_method = "create_checkout" if action == "add_to_checkout" else action

        elif text_part:
            log.info("📝 Text Part Detected: %s", text_part.get("text"))
            action = "search_shopping_catalog"
            internal_method = "search_shopping_catalog"
            payload = {"query": text_part.get("text")}

        else:
            log.error("❌ ERROR: Neither Data nor Text part found!")
            log.error("Inspected Parts: %s", parts)
            return self._create_error_reply(body, "No recognizable part found (text or data).")

        if not internal_method or internal_method not in self.app._handlers:  # noqa: SLF001
            log.error("❌ Unknown Action: %s (Mapped method: %s)", action, internal_method)
            return self._create_error_reply(body, f"Unknown action: {action}")

        try:
            clean_params = payload.copy()
            if "action" in clean_params:
                del clean_params["action"]

            session_id = clean_params.pop("id", None)
            if not session_id and "checkout_id" in clean_params:
                session_id = clean_params.pop("checkout_id")

            if "a2a.ucp.checkout.payment_data" in clean_params:
                clean_params["payment"] = clean_params.pop("a2a.ucp.checkout.payment_data")

            # Handler Call
            log.info("🚀 Executing: %s (Session: %s)", internal_method, session_id)
            result = self.app._call_internal_handler(internal_method, session_id, clean_params)  # noqa: SLF001

            # Result Processing
            result_data = result.model_dump(mode="json", exclude_none=True) if isinstance(result, BaseModel) else result

            response_data_content = {}
            if "line_items" in result_data or "id" in result_data:
                response_data_content["a2a.ucp.checkout"] = result_data
            else:
                response_data_content = result_data

            return JSONResponse(
                self.jsonrpc(
                    body.get("id"),
                    result={
                        "kind": "message",
                        "role": "agent",
                        "messageId": str(uuid.uuid4()),
                        "contextId": context_id,
                        "parts": [{"kind": "data", "data": response_data_content}],
                    },
                )
            )

        except Exception as e:
            log.exception("❌ Error during A2A processing")
            return self._create_error_reply(body, str(e))

    def _create_error_reply(self, original_body: dict[str, Any], error_msg: str) -> JSONResponse:
        return JSONResponse(
            self.error_response(original_body.get("id"), -32603, error_msg),
            status_code=500,
        )
