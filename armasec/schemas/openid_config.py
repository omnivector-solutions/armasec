"""
This module provides a pydantic schema describing openid-configuration data.
"""

from pydantic import ConfigDict, AnyHttpUrl, BaseModel


class OpenidConfig(BaseModel):
    """
    Provides a specification for the objects retrieved from openid_configuration endpoint of the
    OIDC providers. Only includes needed fields for supported Manager instances. Assists with
    validation and item access.

    Attributes:
        issuer:   The URL of the issuer of the tokens.
        jwks_uri: The URI where JWKs can be foun don the OpenID server.
    """

    issuer: AnyHttpUrl
    jwks_uri: AnyHttpUrl
    model_config = ConfigDict(extra="allow")
