""""""

from typing import Literal

from ucp_sdk.models.schemas.service import Base as Service
from ucp_sdk.models.schemas.service import Version

from fastucp.types import AnyUrl, HttpsUrl
from fastucp.version import UCP_VERSION

ServiceT = Literal["rest", "mcp", "a2a", "embedded"]


SCHEMAS: dict[ServiceT, HttpsUrl] = {
    "rest": HttpsUrl(f"https://ucp.dev/{UCP_VERSION.root}/services/shopping/openapi.json"),
    "mcp": HttpsUrl(f"https://ucp.dev/{UCP_VERSION.root}/services/shopping/openrpc.json"),
    "embedded": HttpsUrl(f"https://ucp.dev/{UCP_VERSION.root}/services/shopping/embedded.json"),
}


def make_service(name: ServiceT, endpoint: str | None = None) -> Service:
    """"""
    if endpoint is None and name != "embedded":
        msg = "Endpoint is required for non-embedded services"
        raise ValueError(msg)
    return Service(
        version=Version(UCP_VERSION),
        spec=HttpsUrl(f"https://ucp.dev/{UCP_VERSION.root}/specification/service"),
        transport=name,
        schema=SCHEMAS.get(name),
        endpoint=AnyUrl(endpoint) if endpoint else None,
    )
