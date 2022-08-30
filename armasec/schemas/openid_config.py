"""
This module provides a pydantic schema describing openid-configuration data.
"""
from pydantic import AnyHttpUrl, BaseModel


class OpenidConfig(BaseModel):
    """
    Provides a specification for the objects retrieved from openid_configuration endpoint of the
    OIDC providers. Only includes needed fields for supported Manager instances. Assists with
    validation and item access.
    """

    issuer: AnyHttpUrl
    jwks_uri: AnyHttpUrl

    class Config:
        extra = "allow"
