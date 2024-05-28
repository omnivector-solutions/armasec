"""
This module provides pydantic schemas for JSON Web Keys.
"""

from typing import List, Optional

from pydantic import ConfigDict, BaseModel


class JWK(BaseModel):
    """
    This Model provides a specification for the objects retrieved from JWK endpoints in OIDC
    providers. It also assists with validation and item access.

    Attributes:
        alg: The algorithm to use for hash validation.
        e:   The exponent parameter to use in RS256 hashing
        kid: The "kid" claim to uniquely identify the key.
        kty: The "kty" claim to identify the type of the key.
        n:   The modulus parameter to use in RS256 hashing.
        use: The claim that identifies the intended use of the public key.
        x5c: The X.509 certificate chain parameter
        x5c: The X.509 certificate SHA-1 thumbprint parameter
    """

    alg: str
    e: str
    kid: str
    kty: str
    n: str

    use: Optional[str] = None
    x5c: Optional[List[str]] = None
    x5t: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class JWKs(BaseModel):
    """
    This Model provides a specification for the container object retrieved from JWK endpoints in
    OIDC providers. It also assists with validation and item access.

    Attributes:
        keys: The list of JWKs contained within.
    """

    keys: List[JWK]
