"""
This module provides an abstract base class for algorithmic token decoders
"""
from abc import ABC, abstractmethod
from functools import partial
from typing import Any, Callable, Optional

from jose import jwt

from armasec.exceptions import AuthenticationError
from armasec.token_payload import TokenPayload
from armasec.utilities import log_error, noop


class TokenDecoder(ABC):
    """
    Abstract base class for algorithmic token decoders.
    """

    algorithm: str

    def __init__(
        self,
        debug_logger: Optional[Callable[..., None]] = None,
        decode_options_override: Optional[dict] = None,
    ):
        """
        Initializes a base TokenManager.

        Args:

            openid_config:           The openid_configuration needed for claims such as 'issuer'.
            debug_logger:            A callable, that if provided, will allow debug logging. Should
                                     be passed as a logger method like `logger.debug`
            decode_options_override: Options that can override the default behavior of the jwt
                                     decode method. For example, one can ignore token expiration by
                                     setting this to `{ "verify_exp": False }`
        """
        self.debug_logger = debug_logger if debug_logger else noop
        self.decode_options_override = decode_options_override if decode_options_override else {}

    @abstractmethod
    def get_decode_key(self, token: str) -> Any:
        """
        Retrieve the key that will be needed to decode the token. Override in
        inheriting classes.
        """
        pass

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
            token_payload = TokenPayload.from_dict(payload_dict)
            self.debug_logger(f"Built token_payload as {token_payload}")
            return token_payload
