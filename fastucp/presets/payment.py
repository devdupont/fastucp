""""""

from ucp_sdk.models.schemas.shopping.types.payment_handler_resp import PaymentHandlerResponse

from fastucp.types import HttpsUrl
from fastucp.version import UCP_VERSION


class ShopPay(PaymentHandlerResponse):
    def __init__(self, shop_id: str):
        # Shop Pay spec and schema URLs still reference older UCP version
        version = "2026-01-11"
        config = {"shop_id": shop_id}

        super().__init__(
            id="shop_pay",
            name="com.shopify.pay",
            version=UCP_VERSION,
            spec=HttpsUrl("https://shopify.dev/docs/agents/checkout/shop-pay-handler"),
            config_schema=HttpsUrl(f"https://shopify.dev/ucp/shop-pay-handler/{version}/config.json"),
            instrument_schemas=[HttpsUrl(f"https://shopify.dev/ucp/shop-pay-handler/{version}/instrument.json")],
            config=config,
        )


class GooglePay(PaymentHandlerResponse):
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
            id="gpay",
            name="com.google.pay",
            version=UCP_VERSION,
            spec=HttpsUrl(f"https://pay.google.com/gp/p/ucp/{version}/"),
            config_schema=HttpsUrl(f"https://pay.google.com/gp/p/ucp/{version}/schemas/config.json"),
            instrument_schemas=[
                HttpsUrl(f"https://pay.google.com/gp/p/ucp/{version}/schemas/card_payment_instrument.json")
            ],
            config=config,
        )
