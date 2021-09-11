"""
This module provides a token decoder that uses the RS256 algorithm to check token signatures.
"""
from typing import Any

from jose import jwt

from armasec.exceptions import AuthenticationError
from armasec.schemas.jwks import JWKs
from armasec.token_decoders.base import TokenDecoder


class RS256Decoder(TokenDecoder):
    """
    This decoder verifies a jwt signed with a 256 byte RSA signature.
    """

    algorithm = "RS256"

    def __init__(self, jwks: JWKs, *args, **kwargs):
        """
        Initialize an RS256Manager with its jwks.
        """
        super().__init__(*args, **kwargs)
        self.jwks = jwks

    def get_decode_key(self, token: str) -> Any:
        """
        Overload the base class method. Search for a public keys within the JWKs that matches
        the incoming token's unverified header. Uses it for the decode key.
        Raise AuthenticationError if matching public key cannot be found.
        """
        self.debug_logger("Getting decode key from JWKs")
        unverified_header = jwt.get_unverified_header(token)
        self.debug_logger(f"Extraced unverified header: {unverified_header}")
        kid = unverified_header.get("kid")
        AuthenticationError.require_condition(
            kid,
            "Unverified header doesn't contain 'kid'...not sure how this happened",
        )

        for jwk in self.jwks.keys:
            self.debug_logger(f"Checking key in jwk: {jwk}")
            if jwk.kid == kid:
                self.debug_logger("Key matches unverified header. Using as decode secret.")
                return jwk.dict()

        raise AuthenticationError("Could not find a matching jwk")
