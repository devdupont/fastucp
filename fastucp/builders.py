from dataclasses import dataclass, field
from typing import Any, Self

from pydantic import AnyUrl
from ucp_sdk.models.schemas.shopping.discount_resp import Checkout as _DiscountCheckout
from ucp_sdk.models.schemas.shopping.fulfillment_resp import Checkout as _FulfillmentCheckout
from ucp_sdk.models.schemas.shopping.fulfillment_resp import Fulfillment

from fastucp.core import FastUCP
from fastucp.types import (
    AppliedDiscount,
    # CheckoutResponse as _CheckoutResponse,
    DiscountsObject,
    FulfillmentGroupResponse,
    FulfillmentMethodResponse,
    FulfillmentOptionResponse,
    FulfillmentResponse,
    ItemResponse,
    LineItemResponse,
    Message,
    MessageError,
    PaymentResponse,
    TotalResponse,
)


class CheckoutResponse(_DiscountCheckout, _FulfillmentCheckout):
    """Extends existing CheckoutResponse but adds (apparently) missing fulfillment and discount fields."""


@dataclass
class CheckoutBuilder:
    """Builder pattern to construct a valid UCP CheckoutResponse without dealing with nested Pydantic models manually."""

    app: FastUCP
    session_id: str
    currency: str = "USD"

    line_items: list[LineItemResponse] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    buyer: Any | None = None
    subtotal: int = 0
    links: list[Any] = field(default_factory=list)

    _shipping_options: list[FulfillmentOptionResponse] = field(default_factory=list)
    _discounts: list[AppliedDiscount] = field(default_factory=list)
    _shipping_cost: int = 0
    _discount_amount: int = 0

    def add_item(
        self,
        item_id: str,
        title: str,
        price: int,
        quantity: int,
        img_url: str,
    ) -> Self:
        """Adds a line item and auto-calculates totals."""

        line_total = price * quantity
        self.subtotal += line_total

        li_totals = [TotalResponse(type="subtotal", amount=line_total), TotalResponse(type="total", amount=line_total)]

        self.line_items.append(
            LineItemResponse(
                id=f"li_{len(self.line_items) + 1}",
                item=ItemResponse(id=item_id, title=title, price=price, image_url=AnyUrl(img_url)),
                quantity=quantity,
                totals=li_totals,
            )
        )
        return self

    def set_buyer(self, buyer_data: Any | None) -> Self:
        """Sets the buyer and performs basic validation checks."""
        self.buyer = buyer_data
        email = buyer_data.get("email") if isinstance(buyer_data, dict) else getattr(buyer_data, "email", None)
        if buyer_data and not email:
            self.add_error(code="missing", path="$.buyer.email", message="Email address is required to checkout.")
        return self

    def add_error(self, code: str, path: str, message: str) -> Self:
        """Adds a UCP compliant error message to the response."""
        self.messages.append(
            Message(
                root=MessageError(type="error", code=code, path=path, severity="requires_buyer_input", content=message)
            )
        )
        return self

    def add_shipping_option(self, option_id: str, title: str, amount: int, description: str = "") -> Self:
        """Developer-friendly shipping option addition.

        Automatically sets up the complex Fulfillment hierarchy (Method -> Group -> Option).
        """
        self._shipping_options.append(
            FulfillmentOptionResponse(
                id=option_id,
                title=title,
                description=description,
                totals=[TotalResponse(type="fulfillment", amount=amount)],
            )
        )
        return self

    def select_shipping_option(self, option_id: str) -> Self:
        """Marks a shipping option as 'selected' and adds the amount to the total."""
        for opt in self._shipping_options:
            if opt.id == option_id:
                cost = opt.totals[0].amount
                self._shipping_cost = cost
                self._selected_shipping_id = option_id
                return self
        return self

    def add_discount(self, code: str, amount: int, title: str, priority: int | None = None) -> Self:
        """Applies a discount to the cart."""
        self._discounts.append(AppliedDiscount(code=code, title=title, amount=amount, priority=priority))
        self._discount_amount += amount
        return self

    def build(self) -> CheckoutResponse:
        final_total = self.subtotal + self._shipping_cost - self._discount_amount
        final_total = max(0, final_total)
        cart_totals = [TotalResponse(type="subtotal", amount=self.subtotal)]

        if self._shipping_cost > 0:
            cart_totals.append(TotalResponse(type="fulfillment", amount=self._shipping_cost))

        if self._discount_amount > 0:
            cart_totals.append(TotalResponse(type="discount", amount=self._discount_amount))

        cart_totals.append(TotalResponse(type="total", amount=final_total))

        # 2. Build Fulfillment Object (If exists)
        fulfillment_obj = None
        if self._shipping_options:
            # Automatically creating a default "Shipping Group"
            fulfillment_obj = FulfillmentResponse(
                methods=[
                    FulfillmentMethodResponse(
                        id="method_shipping",
                        type="shipping",
                        line_item_ids=[li.id for li in self.line_items],  # All items
                        groups=[
                            FulfillmentGroupResponse(
                                id="group_default",
                                line_item_ids=[li.id for li in self.line_items],
                                options=self._shipping_options,
                                selected_option_id=getattr(self, "_selected_shipping_id", None),
                            )
                        ],
                    )
                ]
            )

        discounts_obj = None
        if self._discounts:
            discounts_obj = DiscountsObject(applied=self._discounts, codes=[d.code for d in self._discounts if d.code])

        ucp_context = self.app._create_ucp_context(context_type="checkout")  # noqa: SLF001

        return CheckoutResponse(
            ucp=ucp_context,
            id=self.session_id,
            status="ready_for_complete" if not self.messages else "incomplete",
            line_items=self.line_items,
            currency=self.currency,
            totals=cart_totals,
            messages=self.messages if self.messages else None,
            links=self.links,
            payment=PaymentResponse(handlers=self.app.payment_handlers),
            buyer=self.buyer,
            fulfillment=Fulfillment(fulfillment_obj) if fulfillment_obj else None,
            discounts=discounts_obj,
        )
