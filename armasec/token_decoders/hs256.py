"""
This module provides a token decoder that uses the HS256 algorithm to check token signatures.
"""
from typing import Any

from armasec.token_decoders.base import TokenDecoder


class HS256Decoder(TokenDecoder):
    """
    This decoder verifies a jwt signed with a 256 byte RSA signature.
    """

    algorithm = "HS256"

    def __init__(self, secret, *args, **kwargs):
        """
        Initialize an HS256Manager with its secret.
        """
        super().__init__(*args, **kwargs)
        self.secret = secret

    def get_decode_key(self, token: str) -> Any:
        """
        Overload the base class method. Simply return the secret.
        """
        return self.secret
