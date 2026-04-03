from pydantic import AnyUrl
from pydantic.networks import HttpUrl, UrlConstraints
from ucp_sdk.models.schemas.shopping.checkout import Checkout
from ucp_sdk.models.schemas.shopping.checkout_create_request import CheckoutCreateRequest
from ucp_sdk.models.schemas.shopping.checkout_update_request import CheckoutUpdateRequest
from ucp_sdk.models.schemas.shopping.discount import AppliedDiscount, DiscountExtension, DiscountsObject
from ucp_sdk.models.schemas.shopping.order import Order
from ucp_sdk.models.schemas.shopping.payment import Payment
from ucp_sdk.models.schemas.shopping.types.buyer import Buyer
from ucp_sdk.models.schemas.shopping.types.fulfillment import Fulfillment
from ucp_sdk.models.schemas.shopping.types.fulfillment_event import FulfillmentEvent
from ucp_sdk.models.schemas.shopping.types.fulfillment_group import FulfillmentGroup
from ucp_sdk.models.schemas.shopping.types.fulfillment_method import FulfillmentMethod
from ucp_sdk.models.schemas.shopping.types.fulfillment_option import FulfillmentOption
from ucp_sdk.models.schemas.shopping.types.item import Item
from ucp_sdk.models.schemas.shopping.types.line_item import LineItem
from ucp_sdk.models.schemas.shopping.types.line_item_create_request import LineItemCreateRequest
from ucp_sdk.models.schemas.shopping.types.message import Message
from ucp_sdk.models.schemas.shopping.types.message_error import MessageError
from ucp_sdk.models.schemas.shopping.types.payment_instrument import PaymentInstrument
from ucp_sdk.models.schemas.shopping.types.total import Total


class HttpsUrl(HttpUrl):
    """Validate https URL strings."""

    _constraints = UrlConstraints(max_length=2083, allowed_schemes=["https"])


__all__ = [
    "CheckoutCreateRequest",
    "CheckoutUpdateRequest",
    "Checkout",
    "Order",
    "LineItem",
    "LineItemCreateRequest",
    "Item",
    "Total",
    "Message",
    "MessageError",
    "FulfillmentEvent",
    "Fulfillment",
    "FulfillmentMethod",
    "FulfillmentOption",
    "FulfillmentGroup",
    "DiscountExtension",
    "DiscountsObject",
    "AppliedDiscount",
    "Payment",
    "PaymentInstrument",
    "Buyer",
    "AnyUrl",
    "HttpsUrl",
]
