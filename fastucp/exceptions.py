# fastucp/exceptions.py
from typing import Literal


class UCPError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        path: str | None = None,
        severity: Literal["recoverable", "requires_buyer_input", "requires_buyer_review"] = "requires_buyer_input",
        status_code: int = 400,
    ):
        self.code = code
        self.message = message
        self.path = path
        self.severity = severity
        self.status_code = status_code
        super().__init__(message)
