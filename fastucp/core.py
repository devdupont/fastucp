import logging
from collections.abc import Callable
from contextlib import suppress
from typing import Any, Literal, get_type_hints, overload

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import AnyUrl, BaseModel
from ucp_sdk.models._internal import (
    A2a,
    DiscoveryProfile,
    Mcp,
    ResponseCheckout,
    ResponseOrder,
    Rest,
    Services,
    UcpService,
)
from ucp_sdk.models.discovery.profile_schema import Payment, UcpDiscoveryProfile
from ucp_sdk.models.schemas.shopping.types.message import Message
from ucp_sdk.models.schemas.shopping.types.message_error import MessageError
from ucp_sdk.models.schemas.shopping.types.payment_handler_resp import PaymentHandlerResponse

from fastucp.__about__ import __version__ as _fastucp_version
from fastucp.exceptions import UCPError
from fastucp.presets import Capability
from fastucp.protocols.a2a import A2AProtocol
from fastucp.security import UCPSigningMiddleware
from fastucp.version import UCP_VERSION

log = logging.getLogger(__name__)


class FastUCP(FastAPI):
    """FastAPI subclass customized for Universal Commerce Protocol.

    Automatically handles /.well-known/ucp discovery and protocol routing.
    """

    ucp_base_url: str
    ucp_version = UCP_VERSION

    enable_a2a: bool
    enable_mcp: bool
    signing_key: str | None

    capabilities: set[Capability]
    payment_handlers: list[PaymentHandlerResponse]

    _handlers: dict[str, Callable[..., BaseModel | dict]]
    _services: dict[str, UcpService]



    def __init__(
        self,
        base_url: str,
        *,
        title: str = "FastUCP Merchant",
        version: str = "0.1.0",
        enable_mcp: bool = False,
        enable_a2a: bool = False,
        signing_key: str | None = None,
        **kwargs: Any,
    ):
        self._print_banner(title, version)
        super().__init__(title=title, version=version, **kwargs)

        self.base_url = base_url.rstrip("/")

        self.enable_mcp = enable_mcp
        self.enable_a2a = enable_a2a

        self.capabilities = set()
        self.payment_handlers = []
        self._handlers = {}

        self._services = {
            "dev.ucp.shopping": UcpService(
                version=UCP_VERSION,
                spec=AnyUrl(f"https://ucp.dev/{UCP_VERSION.root}/specification/overview"),
                rest=Rest(
                    schema=AnyUrl(f"https://ucp.dev/{UCP_VERSION.root}/services/shopping/openapi.json"),
                    endpoint=AnyUrl(self.base_url),
                ),
            )
        }

        self.add_api_route(
            "/.well-known/ucp",
            self._handle_manifest,
            methods=["GET"],
            response_model=UcpDiscoveryProfile,
            response_model_exclude_none=True,
            tags=["UCP Discovery"],
        )
        self.add_exception_handler(UCPError, self._ucp_exception_handler)  # type: ignore

        if self.enable_mcp:
            from fastucp.protocols.mcp import MCPProtocol

            self.mcp_protocol = MCPProtocol(self)

            self.add_api_route("/mcp", self.mcp_protocol.handle_request, methods=["POST"], tags=["UCP Protocol: MCP"])
            log.info("🤖 MCP Server Ready at: %s/mcp", self.base_url)

        if self.enable_a2a:
            self.a2a_protocol = A2AProtocol(self)
            self.add_api_route(
                "/.well-known/agent-card.json",
                self.a2a_protocol.handle_agent_card,
                methods=["GET"],
                tags=["UCP Protocol: A2A"],
            )
            self.add_api_route(
                "/agent/message", self.a2a_protocol.handle_message, methods=["POST"], tags=["UCP Protocol: A2A"]
            )
            log.info("✅ A2A Protocol Enabled (/agent/message)")

        if signing_key:
            self.add_middleware(UCPSigningMiddleware, private_key_json=signing_key)
            log.info("🔒 Response Signing Enabled (JWS)")

    @staticmethod
    def _print_banner(title: str, version: str) -> None:
        cyan = "\033[96m"
        green = "\033[92m"
        bold = "\033[1m"
        reset = "\033[0m"

        banner = rf"""{cyan}{bold}
        ------------------------------------------------------
               ______        _    _    _  _____ ______
              |  ____|      | |  | |  | |/ ____|  __  \
              | |__ __ _ ___| |__| |  | | |    | |__) |
              |  __/ _` / __|  __| |  | | |    | |____/
              | | | (_| \__ \ |_ | |__| | |____| |
              |_|  \__,_|___/\__|\______/\_____|_|

        -------------------------------------------------------

        {reset}

        {green}
        🤖 {title} v{version}
        ⚡️ FastUCP v{_fastucp_version}
        🛍️  Universal Commerce Protocol v{UCP_VERSION.root}
        {reset}
        """

        log.info(banner)

    async def _ucp_exception_handler(self, _: Request, exc: UCPError) -> JSONResponse:
        error_payload = Message(
            root=MessageError(type="error", code=exc.code, path=exc.path, severity=exc.severity, content=exc.message)
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"messages": [error_payload.model_dump(exclude_none=True, mode="json")]},
        )

    def add_payment_handler(self, handler: PaymentHandlerResponse) -> None:
        self.payment_handlers.append(handler)

    def _register_capability(self, capability: Capability) -> None:
        self.capabilities.add(capability)

    @overload
    def _create_ucp_context(self, context_type: Literal["checkout"]) -> ResponseCheckout:
        ...

    @overload
    def _create_ucp_context(self, context_type: Literal["order"]) -> ResponseOrder:
        ...

    def _create_ucp_context(self, context_type: str = "checkout") -> ResponseCheckout | ResponseOrder:
        active_caps = [c.value.as_response() for c in self.capabilities]
        if context_type == "order":
            return ResponseOrder(version=UCP_VERSION, capabilities=active_caps)
        return ResponseCheckout(version=UCP_VERSION, capabilities=active_caps)

    def _handle_manifest(self) -> UcpDiscoveryProfile:
        shopping_service = self._services["dev.ucp.shopping"]

        # Manifest update logic
        if self.enable_mcp:
            shopping_service.mcp = Mcp(
                schema=AnyUrl(f"https://ucp.dev/{UCP_VERSION.root}/services/shopping/mcp.openrpc.json"),
                # Critical: Writing our /mcp address to the Discovery file
                endpoint=AnyUrl(f"{self.ucp_base_url}/mcp"),
            )
        if self.enable_a2a:
            shopping_service.a2a = A2a(endpoint=AnyUrl(f"{self.ucp_base_url}/.well-known/agent-card.json"))

        capabilities = [c.value.as_discovery() for c in self.capabilities]

        return UcpDiscoveryProfile(
            ucp=DiscoveryProfile(
                version=UCP_VERSION, services=Services(root=self._services), capabilities=capabilities
            ),
            payment=Payment(handlers=self.payment_handlers) if self.payment_handlers else None,
        )

    # --- Decorators ---
    def checkout(self, func: Callable | None = None, /, *, path: str = "/checkout-sessions") -> Callable:
        self._register_capability(Capability.DISCOVERY)

        def decorator(func: Callable) -> Callable:
            self.add_api_route(path, func, methods=["POST"], response_model_exclude_none=True, tags=["UCP Shopping"])
            self._handlers["create_checkout"] = func
            return func

        if callable(func):
            return decorator(func)

        return decorator

    def update_checkout(self, func: Callable | None = None, /, *, path: str = "/checkout-sessions/{id}") -> Callable:
        def decorator(func: Callable) -> Callable:
            self.add_api_route(path, func, methods=["PATCH"], response_model_exclude_none=True, tags=["UCP Shopping"])
            self._handlers["update_checkout"] = func
            return func

        if callable(func):
            return decorator(func)

        return decorator

    def complete_checkout(
        self, func: Callable | None = None, /, *, path: str = "/checkout-sessions/{id}/complete"
    ) -> Callable:
        self._register_capability(Capability.ORDER)

        def decorator(func: Callable) -> Callable:
            self.add_api_route(path, func, methods=["POST"], response_model_exclude_none=True, tags=["UCP Shopping"])
            self._handlers["complete_checkout"] = func
            return func

        if callable(func):
            return decorator(func)
        return decorator

    def _call_internal_handler(
        self, method_name: str, session_id: str | None, params: dict[str, Any]
    ) -> BaseModel | dict:
        """
        Bridge method for other protocols (MCP, A2A) to call internal functions.
        SMART VERSION: Analyzes function parameters and populates Pydantic models automatically.
        """
        if method_name not in self._handlers:
            msg = f"Method {method_name} not registered"
            raise ValueError(msg)

        handler_func = self._handlers[method_name]

        import inspect

        sig = inspect.signature(handler_func)
        func_params = sig.parameters
        type_hints = get_type_hints(handler_func)

        if session_id:
            if "checkout_id" in func_params:
                params["checkout_id"] = session_id
            elif "session_id" in func_params:
                params["session_id"] = session_id
            elif "id" in func_params and method_name != "create_checkout":
                # In create_checkout, 'id' is usually inside the payload, avoid conflict
                params["id"] = session_id

        final_kwargs = {}

        for name in func_params:
            if name in params:
                value = params[name]

                if name in type_hints:
                    model_class = type_hints[name]
                    if isinstance(model_class, type) and issubclass(model_class, BaseModel) and isinstance(value, dict):
                        try:
                            value = model_class(**value)
                        except Exception:
                            log.exception("⚠️ Model conversion warning for %s", name)

                final_kwargs[name] = value

            elif name in type_hints:
                model_class = type_hints[name]
                if isinstance(model_class, type) and issubclass(model_class, BaseModel):
                    with suppress(Exception):
                        final_kwargs[name] = model_class(**params)

        return handler_func(**final_kwargs)

    def discovery(self, func: Callable | None = None, /, *, path: str = "/products/search") -> Callable:
        """
        Decorator recording Discovery capabilities such as product search.
        """

        self._register_capability(Capability.DISCOVERY)

        def decorator(func: Callable) -> Callable:
            self.add_api_route(path, func, methods=["POST"], response_model_exclude_none=True, tags=["UCP Discovery"])

            self._handlers[func.__name__] = func
            return func

        if callable(func):
            return decorator(func)
        return decorator


# TODO: Add more decorators for other capabilities (e.g. discount, fulfillment, buyer_consent etc.) which extend checkout

# TODO: Support multiple version specs in the same app (e.g. v2026-01-11 and v2026-01-23) with version negotiation
