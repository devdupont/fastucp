""""""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastucp.core import FastUCP


class Protocol:

    def __init__(self, app: "FastUCP") -> None:
        self.app = app

    @staticmethod
    def jsonrpc(req_id: Any, *, result: dict | None = None, error: dict | None = None) -> dict:
        data: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id}
        if result is not None:
            data["result"] = result
        if error is not None:
            data["error"] = error
        return data

    def error_response(self, req_id: Any, code: int, message: str) -> dict:
        return self.jsonrpc(req_id, error={"code": code, "message": message})
