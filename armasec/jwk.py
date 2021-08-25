from typing import List

from pydantic import BaseModel


class JWK(BaseModel):
    """
    Provides a specification for the objects retrieved from JWK endpoints in OIDC providers. Assists
    with validation and item access
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

