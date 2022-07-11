"""
This module provides a pydantic schema describing Armasec's configuration parameters.
"""
from typing import Any, Dict, List, Optional, Set, Union

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
        ),
    )
    match_keys: Dict[
        str, Union[str, List[Any], Dict[Any, Any], Set[Any], bool, int, float]
    ] = Field(
        dict(),
        description=(
            "Dictionary of key-value pair to match in the token when decoding it. It will"
            " raise 403 in case the input key-value pair cannot be found in the token."
        ),
    )
