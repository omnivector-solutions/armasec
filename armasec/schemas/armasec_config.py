"""
This module provides a pydantic schema describing Armasec's configuration parameters.
"""
from typing import Optional

from pydantic import BaseModel, Field


class DomainConfig(BaseModel):
    """
    This model provides a specification for the input domains to authenticate against.
    It expects the domain indeed and the audience to refer to.
    """

    domain: str = Field(str(), description="The OIDC domain where resources are loaded.")
    audience: Optional[str] = Field(None, description="Optional designation of the token audience.")
    algorithm: str = Field(
        "RS256", description="The the algorithm to use for decoding. Defaults to RS256."
    )
    use_https: bool = Field(
        True,
        description=(
            "If falsey, use ``http`` when pulling openid config "
            "from the OIDC server instead of ``https`` (the default)."
        )
    )
