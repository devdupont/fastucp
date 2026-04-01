""""""

from enum import Enum

# Pydantic wants Version to be here for schema generation, even if it's not used directly in the code.
from ucp_sdk.models._internal import (
    Base,
    Discovery,
    Response,
    Version,  # noqa
)

from fastucp.types import HttpsUrl
from fastucp.version import UCP_VERSION


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
            version=UCP_VERSION,
            spec=_spec_url(capability),
            schema=_schema_url(capability),
            extends=extends,
        )


def _spec_url(name: str) -> HttpsUrl:
    return HttpsUrl(f"https://ucp.dev/{UCP_VERSION.root}/specification/{name}")


def _schema_url(name: str) -> HttpsUrl:
    return HttpsUrl(f"https://ucp.dev/{UCP_VERSION.root}/schemas/shopping/{name}.json")


class Capability(Enum):
    DISCOVERY = _Capability.from_type("discovery")
    CHECKOUT = _Capability.from_type("checkout")
    ORDER = _Capability.from_type("order")
    DISCOUNT = _Capability.from_type("discount", extends="dev.ucp.shopping.checkout")
    FULFILLMENT = _Capability.from_type("fulfillment", extends="dev.ucp.shopping.checkout")
    BUYER_CONSENT = _Capability.from_type("buyer_consent", extends="dev.ucp.shopping.checkout")
