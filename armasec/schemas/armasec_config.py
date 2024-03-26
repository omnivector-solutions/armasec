"""
This module provides a pydantic schema describing Armasec's configuration parameters.
"""

from typing import Any, Dict, List, Optional, Set, Union

import snick
from pydantic import BaseModel, Field


class DomainConfig(BaseModel):
    """
    This model provides a specification for the input domains to authenticate against.
    It expects the domain indeed and the audience to refer to.

    Attributes:
        domain:     The OIDC domain from which resources are loaded.
        audience:   Optional designation of the token audience.
        algorithm:  The Algorithm to use for decoding. Defaults to RS256.
        use_https:  If true, use `https` for URLs. Otherwise use `http`
        match_keys: Dictionary of k/v pairs to match in the token when decoding it.
    """

    domain: str = Field(str(), description="The OIDC domain where resources are loaded.")
    audience: Optional[str] = Field(None, description="Optional designation of the token audience.")
    algorithm: str = Field(
        "RS256", description="The the algorithm to use for decoding. Defaults to RS256."
    )
    use_https: bool = Field(
        True,
        description=snick.unwrap(
            """
            If falsey, use ``http`` when pulling openid config from the OIDC server
            instead of ``https`` (the default).
            """,
        ),
    )
    match_keys: Dict[str, Union[str, List[Any], Dict[Any, Any], Set[Any], bool, int, float]] = (
        Field(
            dict(),
            description=snick.unwrap(
                """
            Dictionary of key-value pair to match in the token when decoding it. It will
            raise 403 in case the input key-value pair cannot be found in the token.
            """
            ),
        )
    )
    payload_claim_mapping: Optional[Dict[str, Any]] = Field(
        None,
        description=snick.unwrap(
            """
            Optional mappings that are applied to map claims to top-level properties of
            TokenPayload. See docs for `TokenDecoder` for more info.
            """
        ),
    )
