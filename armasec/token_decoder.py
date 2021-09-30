"""
This module provides an abstract base class for algorithmic token decoders
"""
from functools import partial
from typing import Callable, Optional

from jose import jwt

from armasec.exceptions import AuthenticationError
from armasec.schemas.jwks import JWKs
from armasec.token_payload import TokenPayload
from armasec.utilities import log_error, noop


class TokenDecoder:
    """
    Decoder class used to decode tokens given an algorithm and jwks.
    """

    algorithm: str

    def __init__(
        self,
        jwks: JWKs,
        algorithm: str = "RS256",
        debug_logger: Optional[Callable[..., None]] = None,
        decode_options_override: Optional[dict] = None,
    ):
        """
        Initializes a TokenDecoder.

        Args:

            algorithm:               The algorithm to use for decoding. Defaults to RS256.
            jwks:                    JSON web keys object holding the public keys for decoding.
            openid_config:           The openid_configuration needed for claims such as 'issuer'.
            debug_logger:            A callable, that if provided, will allow debug logging. Should
                                     be passed as a logger method like `logger.debug`
            decode_options_override: Options that can override the default behavior of the jwt
                                     decode method. For example, one can ignore token expiration by
                                     setting this to `{ "verify_exp": False }`
        """
        self.algorithm = algorithm
        self.jwks = jwks
        self.debug_logger = debug_logger if debug_logger else noop
        self.decode_options_override = decode_options_override if decode_options_override else {}

    def get_decode_key(self, token: str) -> dict:
        """
        Search for a public keys within the JWKs that matches the incoming token's unverified
        header. Uses it for the decode key.  Raise AuthenticationError if matching public key cannot
        be found.
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

    def decode(self, token: str, **claims) -> TokenPayload:
        """
        Decodes a jwt into a TokenPayload while checking signatures and claims.
        """
        self.debug_logger(f"Attempting to decode '{token}'")
        self.debug_logger(f"  checking claims: {claims}")
        with AuthenticationError.handle_errors(
            "Failed to decode token string",
            do_except=partial(log_error, self.debug_logger),
        ):
            payload_dict = dict(
                jwt.decode(
                    token,
                    self.get_decode_key(token),
                    algorithms=[self.algorithm],
                    options=self.decode_options_override,
                    **claims,
                )
            )
            self.debug_logger(f"Payload dictionary is {payload_dict}")
            self.debug_logger("Attempting to convert to TokenPayload")
            token_payload = TokenPayload(**payload_dict)
            self.debug_logger(f"Built token_payload as {token_payload}")
            return token_payload
