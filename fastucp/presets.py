"""Common presets for UCP capabilities and handlers."""

from enum import Enum

from ucp_sdk.models._internal import Base, Discovery, Response, Version
from ucp_sdk.models.schemas.shopping.types.payment_handler_resp import PaymentHandlerResponse

from fastucp.types import HttpsUrl

_UCP_VERSION = Version(root="2026-01-11")


class _Capability(Base):
    """Extends Discovery model to export as Response."""

    def as_discovery(self) -> Discovery:
        return Discovery(
            name=self.name,
            version=self.version,
            spec=self.spec,
            schema=self.schema_,
            extends=self.extends,
            config=self.config,
        )

    def as_response(self) -> Response:
        return Response(
            name=self.name,
            version=self.version,
            spec=self.spec,
            schema=self.schema_,
            extends=self.extends,
            config=self.config,
        )

    @classmethod
    def from_type(cls, capability: str, extends: str | None = None) -> "_Capability":
        return cls(
            name=f"dev.ucp.shopping.{capability}",
            version=_UCP_VERSION,
            spec=_spec_url(capability),
            schema=_schema_url(capability),
            extends=extends,
        )


def _spec_url(name: str) -> HttpsUrl:
    return HttpsUrl(f"https://ucp.dev/{_UCP_VERSION.root}/specification/{name}")


def _schema_url(name: str) -> HttpsUrl:
    return HttpsUrl(f"https://ucp.dev/{_UCP_VERSION.root}/schemas/shopping/{name}.json")


class Capability(Enum):
    DISCOVERY = _Capability.from_type("discovery")
    CHECKOUT = _Capability.from_type("checkout")
    ORDER = _Capability.from_type("order")
    DISCOUNT = _Capability.from_type("discount", extends="dev.ucp.shopping.checkout")
    FULFILLMENT = _Capability.from_type("fulfillment", extends="dev.ucp.shopping.checkout")
    BUYER_CONSENT = _Capability.from_type("buyer_consent", extends="dev.ucp.shopping.checkout")


class GooglePay(PaymentHandlerResponse):
    def __init__(
        self, merchant_name: str, merchant_id: str, gateway: str, gateway_merchant_id: str, environment: str = "TEST"
    ):
        config = {
            "api_version": 2,
            "api_version_minor": 0,
            "environment": environment,
            "merchant_info": {"merchant_name": merchant_name, "merchant_id": merchant_id},
            "allowed_payment_methods": [
                {
                    "type": "CARD",
                    "parameters": {
                        "allowed_auth_methods": ["PAN_ONLY", "CRYPTOGRAM_3DS"],
                        "allowed_card_networks": ["VISA", "MASTERCARD"],
                    },
                    "tokenization_specification": {
                        "type": "PAYMENT_GATEWAY",
                        "parameters": {"gateway": gateway, "gatewayMerchantId": gateway_merchant_id},
                    },
                }
            ],
        }

        super().__init__(
            id="gpay",
            name="com.google.pay",
            version=Version(root="2026-01-11"),
            spec=HttpsUrl("https://pay.google.com/gp/p/ucp/2026-01-11/"),
            config_schema=HttpsUrl("https://pay.google.com/gp/p/ucp/2026-01-11/schemas/config.json"),
            instrument_schemas=[
                HttpsUrl("https://pay.google.com/gp/p/ucp/2026-01-11/schemas/card_payment_instrument.json")
            ],
            config=config,
        )
