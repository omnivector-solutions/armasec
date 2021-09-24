from typing import Callable, Optional, Union

from fastapi.security.utils import get_authorization_scheme_param
from starlette.datastructures import Headers

from armasec.exceptions import AuthenticationError
from armasec.schemas import OpenidConfig
from armasec.token_decoder import TokenDecoder
from armasec.token_payload import TokenPayload
from armasec.utilities import noop


class TokenManager:
    """
    Handle auth via a TokenDecoder and manage extraction from request headers and serialization into
    TokenPayload instances.
    """

    auth_scheme = "bearer"
    header_key = "Authorization"

    def __init__(
        self,
        openid_config: OpenidConfig,
        token_decoder: TokenDecoder,
        audience: Optional[str] = None,
        debug_logger: Optional[Callable[..., None]] = None,
        decode_options_override: Optional[dict] = None,
    ):
        """
        Initializes a base TokenManager.

        Args:

            openid_config:           The openid_configuration needed for claims such as 'issuer'.
            token_decoder:           The decoder used to verify jwts
            debug_logger:            A callable, that if provided, will allow debug logging. Should
                                     be passed as a logger method like `logger.debug`
            decode_options_override: Options that can override the default behavior of the jwt
                                     decode method. For example, one can ignore token expiration by
                                     setting this to `{ "verify_exp": False }`
        """
        self.audience = audience
        self.debug_logger = debug_logger if debug_logger else noop
        self.decode_options_override = decode_options_override if decode_options_override else {}

        self.openid_config = openid_config
        self.token_decoder = token_decoder

    def unpack_token_from_header(self, headers: Union[Headers, dict]) -> str:
        """
        Unpacks a jwt from a request header.
        """
        self.debug_logger(f"Attempting to unpack token from headers {headers}")
        auth_str = headers.get(self.header_key)
        self.debug_logger(f"Got {auth_str} using header key {self.header_key}")
        AuthenticationError.require_condition(
            auth_str,
            f"Could not find auth header at {self.header_key}",
        )
        auth_str = str(auth_str)

        self.debug_logger("Attempting to get authorization scheme")
        (scheme, token) = get_authorization_scheme_param(auth_str)
        self.debug_logger(f"Auth scheme is {scheme} and token is {token}")
        AuthenticationError.require_condition(
            scheme and token,
            f"Could not extract scheme ('{self.auth_scheme}') from token '{token}'",
        )
        AuthenticationError.require_condition(
            scheme.lower() == self.auth_scheme,
            f"Invalid auth scheme '{scheme}': expected '{self.auth_scheme}'",
        )
        return token

    def extract_token_payload(self, headers: Union[Headers, dict]) -> TokenPayload:
        """
        Retrieves a token from a request header and decodes it into a TokenPayload.
        """
        token = self.unpack_token_from_header(headers)
        token_payload = self.token_decoder.decode(token, audience=self.audience)
        return token_payload
