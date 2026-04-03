""""""

from pydantic import BaseModel, ConfigDict
from ucp_sdk.models.schemas.ucp import ReverseDomainName


class NamedEntity(BaseModel):
    """"""

    name: ReverseDomainName

    model_config = ConfigDict(frozen=True)
