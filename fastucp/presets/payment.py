""""""

from ucp_sdk.models.schemas.payment_handler import Base, ResponseSchema, Version

from fastucp.presets.base import NamedEntity, ReverseDomainName
from fastucp.types import HttpsUrl
from fastucp.version import UCP_VERSION


class Payment(Base, NamedEntity):
    def as_response(self) -> ResponseSchema:
        return ResponseSchema(
            id=self.id,
            version=self.version,
            spec=self.spec,
            schema=self.schema_,
            config=self.config,
        )


class ShopPay(Payment):
    """"""

    def __init__(self, shop_id: str):
        # Shop Pay spec and schema URLs still reference older UCP version
        version = "2026-01-11"
        config = {"shop_id": shop_id}

        super().__init__(
            name=ReverseDomainName("com.shopify.pay"),
            id="shop_pay",
            version=Version(UCP_VERSION),
            spec=HttpsUrl("https://shopify.dev/docs/agents/checkout/shop-pay-handler"),
            # TODO: sdk may change this back to schema_config for spec conform
            schema=HttpsUrl(f"https://shopify.dev/ucp/shop-pay-handler/{version}/config.json"),
            # TODO: generated sdk missed this field ???
            # instrument_schemas=[HttpsUrl(f"https://shopify.dev/ucp/shop-pay-handler/{version}/instrument.json")],
            config=config,
        )


class GooglePay(Payment):
    """"""

    def __init__(
        self, merchant_name: str, merchant_id: str, gateway: str, gateway_merchant_id: str, environment: str = "TEST"
    ):
        # Google Pay spec and schema URLs still reference older UCP version
        version = "2026-01-11"
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
            name=ReverseDomainName("com.google.pay"),
            id="gpay",
            version=Version(UCP_VERSION),
            spec=HttpsUrl(f"https://pay.google.com/gp/p/ucp/{version}/"),
            schema=HttpsUrl(f"https://pay.google.com/gp/p/ucp/{version}/schemas/config.json"),
            # instrument_schemas=[
            #     HttpsUrl(f"https://pay.google.com/gp/p/ucp/{version}/schemas/card_payment_instrument.json")
            # ],
            config=config,
        )
