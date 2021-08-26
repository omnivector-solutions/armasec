from traceback import format_tb
from types import TracebackType
from typing import Callable, List, Optional, Union

from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt
from snick import dedent
from starlette.datastructures import Headers

from armasec.exceptions import AuthenticationError
from armasec.token_payload import TokenPayload


def noop(*args, **kwargs):
    """
    This is a no-op function that will be used if no debug_logger is passed to the manager.
    """
    pass


class TokenManager:
    """
    Manages auth via jwt and manages extraction from request headers and serialization into
    TokenPayload instances.
    """

    auth_scheme = "bearer"
    header_key = "Authorization"

    def __init__(
        self,
        secret: str,
        algorithm: str,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        debug_logger: Callable[..., None] = noop,
    ):
        self.secret = secret
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.debug_logger = debug_logger

    def log_error(self, err: Exception, final_message: str, trace: TracebackType):
        """
        Logs an en error with the supplied message, a string representation of the error, and its
        traceback. If no debug_logger is supplied, it will just return without doing anything.
        """
        if not self.debug_logger:
            return

        message_template = dedent(
            """
            {final_message}

            Error:
            ______
            {err}

            Traceback:
            ----------
            {trace}
        """
        )

        self.debug_logger(
            message_template.format(
                final_message=final_message,
                err=str(err),
                trace="\n".join(format_tb(trace)),
            )
        )

    async def _decode_to_payload_dict(self, token: str) -> dict:
        """
        Invokes decoding. Should be overridden by classes that need to apply more decoding logic.
        """
        return dict(
            jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
            )
        )

    async def decode(self, token: str) -> TokenPayload:
        """
        Decodes a jwt into a TokenPayload while checking signatures and claims.
        """
        self.debug_logger(f"Attempting to decode '{token}'")
        with AuthenticationError.handle_errors(
            "Failed to decode token string",
            do_except=self.log_error,
        ):
            payload_dict = await self._decode_to_payload_dict(token)
            self.debug_logger(f"Payload dictionary is {payload_dict}")
            self.debug_logger("Attempting to convert to TokenPayload")
            token_payload = TokenPayload.from_dict(payload_dict)
            self.debug_logger(f"Built token_payload as {token_payload}")
            return token_payload

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

    async def extract_token_payload(self, headers: Union[Headers, dict]) -> TokenPayload:
        """
        Retrieves a token from a request header and decodes it into a TokenPayload.
        """
        token = self.unpack_token_from_header(headers)
        token_payload = await self.decode(token)
        return token_payload


class TestTokenManager(TokenManager):
    """
    This is a special TokenManager that can be used in tests to produce jwts or pack headers.
    """

    def encode_jwt(
        self,
        token_payload: TokenPayload,
        permissions_override: Optional[List[str]] = None,
        secret_override: Optional[str] = None,
    ):
        """
        Encodes a jwt based on a TokenPayload

        Adds any supplied scopes to a "permissions" claim in the jwt

        The ``secret_override`` parameter allows you to encode a jwt using a different secret. Any
        tokens produced in this way will not be decodable by this manager
        """
        claims = dict(
            **token_payload.to_dict(),
            iss=self.issuer,
            aud=self.audience,
        )
        if permissions_override is not None:
            claims["permissions"] = permissions_override
        return jwt.encode(
            claims,
            self.secret if not secret_override else secret_override,
            algorithm=self.algorithm,
        )

    def pack_header(self, *encode_jwt_args, **encode_jwt_kwargs):
        """
        Produces a header including a jwt that could be attached to a request.
        """
        token = self.encode_jwt(*encode_jwt_args, **encode_jwt_kwargs)
        return {self.header_key: f"{self.auth_scheme} {token}"}
