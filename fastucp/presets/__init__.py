"""Common presets for UCP capabilities and handlers."""

from fastucp.presets.capability import (
    AP2_MANDATES,
    BUYER_CONSENT,
    CHECKOUT,
    DISCOUNT,
    DISCOVERY,
    FULFILLMENT,
    ORDER,
    Capability,
)
from fastucp.presets.payment import GooglePay, Payment, ShopPay

__all__ = [
    "Capability",
    "CHECKOUT",
    "DISCOVERY",
    "DISCOUNT",
    "FULFILLMENT",
    "ORDER",
    "BUYER_CONSENT",
    "AP2_MANDATES",
    "Payment",
    "GooglePay",
    "ShopPay",
]
