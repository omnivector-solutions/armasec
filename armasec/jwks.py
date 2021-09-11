"""
This module provides pydantic schemas for JSON Web Keys.
"""
from typing import List

from pydantic import BaseModel


class JWK(BaseModel):
    """
    This Model provides a specification for the objects retrieved from JWK endpoints in OIDC
    providers. It also assists with validation and item access.
    """

    alg: str
    e: str
    kid: str
    kty: str
    n: str
    use: str
    x5c: List[str]
    x5t: str

    class Config:
        extra = "allow"


class JWKs(BaseModel):
    """
    This Model provides a specification for the container object retrieved from JWK endpoints in
    OIDC providers. It also assists with validation and item access.
    """

    keys: List[JWK]
