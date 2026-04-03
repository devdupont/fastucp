""""""

from ucp_sdk.models.schemas.capability import Base, ResponseSchema, Version

from fastucp.presets.base import NamedEntity, ReverseDomainName
from fastucp.types import HttpsUrl
from fastucp.version import UCP_VERSION


class Capability(Base, NamedEntity):
    """"""

    # def as_discovery(self) -> Discovery:
    #     return Discovery(
    #         name=self.name,
    #         version=self.version,
    #         spec=self.spec,
    #         schema=self.schema_,
    #         extends=self.extends,
    #         config=self.config,
    #     )

    def as_response(self) -> ResponseSchema:
        return ResponseSchema(
            version=self.version,
            spec=self.spec,
            schema=self.schema_,
            extends=self.extends,
            config=self.config,
        )

    @classmethod
    def from_type(cls, capability: str, extends: str | None = None, schema_name: str | None = None) -> "Capability":
        return cls(
            name=ReverseDomainName(f"com.ucp.shopping.{capability}"),
            version=Version(UCP_VERSION),
            spec=HttpsUrl(f"https://ucp.dev/{UCP_VERSION.root}/specification/{capability}"),
            schema=HttpsUrl(f"https://ucp.dev/{UCP_VERSION.root}/schemas/shopping/{schema_name or capability}.json"),
            extends=extends,
        )


DISCOVERY = Capability.from_type("discovery")
CHECKOUT = Capability.from_type("checkout")
ORDER = Capability.from_type("order")
DISCOUNT = Capability.from_type("discount", extends="dev.ucp.shopping.checkout")
FULFILLMENT = Capability.from_type("fulfillment", extends="dev.ucp.shopping.checkout")
BUYER_CONSENT = Capability.from_type("buyer_consent", extends="dev.ucp.shopping.checkout")
AP2_MANDATES = Capability.from_type("ap2_mandates", extends="dev.ucp.shopping.checkout", schema_name="ap2_mandate")
