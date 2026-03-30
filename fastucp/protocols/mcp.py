import inspect
import json
import logging
from typing import TypedDict, get_type_hints

from fastapi import Request
from pydantic import BaseModel

from fastucp.protocols.protocol import Protocol

log = logging.getLogger(__name__)


_PARAM_TYPES = {
    str: "string",
    int: "integer",
    bool: "boolean",
    dict: "object",
    float: "number",
}


class InputSchema(TypedDict):
    type: str
    properties: dict[str, dict]
    required: list[str]


class MCPProtocol(Protocol):
    async def handle_request(self, request: Request) -> dict:
        try:
            if request.method == "GET":
                return {
                    "status": "online",
                    "message": "MCP Server is running. Please use POST request with JSON-RPC payload.",
                }

            payload = await request.json()
        except Exception:  # noqa: BLE001
            return self.error_response(None, -32700, "Parse error: Invalid JSON was received by the server.")

        method = payload.get("method")
        params = payload.get("params", {})
        req_id = payload.get("id")

        log.info("📡 MCP Request: %s", method)

        if method == "initialize":
            return self.jsonrpc(
                req_id,
                result={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": self.app.title, "version": "0.1.2"},
                },
            )

        if method == "notifications/initialized":
            return self.jsonrpc(req_id, result={})

        if method == "tools/list":
            tools = []
            for name, func in self.app._handlers.items():  # noqa: SLF001
                description = (func.__doc__ or "UCP Operation").strip()

                input_schema: InputSchema = {"type": "object", "properties": {}, "required": []}
                type_hints = get_type_hints(func)
                sig = inspect.signature(func)

                for param_name, param in sig.parameters.items():
                    if param_name in ["self", "request", "ucp_agent"]:
                        continue
                    json_type = _PARAM_TYPES.get(type_hints.get(param_name, str), "string")
                    input_schema["properties"][param_name] = {
                        "type": json_type,
                        "description": f"Parameter: {param_name}",
                    }
                    if param.default == inspect.Parameter.empty:
                        input_schema["required"].append(param_name)

                tools.append({"name": name, "description": description, "inputSchema": input_schema})

            return self.jsonrpc(req_id, result={"tools": tools})

        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            log.info("🛠️  Tool Call: %s -> Args: %s", tool_name, tool_args)

            if tool_name not in self.app._handlers:  # noqa: SLF001
                return self.error_response(req_id, -32601, f"Tool not found: {tool_name}")

            try:
                session_id = tool_args.get("session_id") or tool_args.get("checkout_id") or tool_args.get("id")

                result = self.app._call_internal_handler(tool_name, session_id, tool_args)  # noqa: SLF001

                if isinstance(result, BaseModel):
                    result_data = result.model_dump(mode="json", exclude_none=True)
                else:
                    result_data = result

                json_string = json.dumps(result_data)
            except Exception as e:
                log.exception("❌ Error during MCP tool execution")
                return self.jsonrpc(
                    req_id,
                    result={"content": [{"type": "text", "text": f"Error executing tool: {e!s}"}], "isError": True},
                )
            return self.jsonrpc(
                req_id, result={"content": [{"type": "text", "text": json_string}], "_raw": result_data}
            )

        return self.error_response(req_id, -32601, f"Method not found: {method}")
