import logging
from collections.abc import Awaitable, Callable

from jwcrypto import jwk, jws
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

log = logging.getLogger(__name__)


class UCPSigningMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, private_key_json: str):
        super().__init__(app)

        self.key = jwk.JWK.from_json(private_key_json)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        if response.headers.get("content-type") == "application/json":
            response_body = [section async for section in response.body_iterator]  # type: ignore
            # Rewind stream
            response.body_iterator = iter(response_body)  # type: ignore
            body_bytes = b"".join(response_body)

            try:
                signer = jws.JWS(body_bytes)
                signer.add_signature(
                    self.key,
                    alg="ES256",  # UCP standard is usually ES256
                    protected={"alg": "ES256", "kid": self.key.key_id},
                )

                signature = signer.serialize(compact=True)
                response.headers["UCP-Signature"] = signature

            except Exception:
                log.exception("⚠️ Signing Error")

        return response
