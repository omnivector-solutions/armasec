from typing import Callable, Iterable, Optional

from fastapi import HTTPException, status
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.api_key import APIKeyBase
from starlette.requests import Request

from armasec.openid_config_loader import OpenidConfigLoader
from armasec.token_decoder import TokenDecoder
from armasec.token_manager import TokenManager
from armasec.token_payload import TokenPayload
from armasec.utilities import noop


class TokenSecurity(APIKeyBase):
    """
    An injectable Security class that returns a TokenPayload when used with Depends().
    """

    manager: Optional[TokenManager]

    def __init__(
        self,
        domain: str,
        audience: Optional[str] = None,
        algorithm: str = "RS256",
        scopes: Optional[Iterable[str]] = None,
        debug_logger: Optional[Callable[[str], None]] = noop,
        debug_exceptions: bool = False,
    ):
        """
        Initializes the TokenSecurity instance.

        Args:
            domain:           The OIDC domain where resources are loaded
            audience:         Optional designation of the token audience.
            algorithm:        The the algorithm to use for decoding. Defaults to RS256.
            scopes:           Optional permissions scopes that should be checked
            debug_logger:     A callable, that if provided, will allow debug logging. Should be
                              passed as a logger method like `logger.debug`
            debug_exceptions: If True, raise original exceptions. Should only be used in a testing
                              or debugging context.
        """
        self.domain = domain
        self.audience = audience
        self.algorithm = algorithm
        self.scopes = scopes

        self.debug_logger = debug_logger
        self.debug_exceptions = debug_exceptions

        # Settings needed for FastAPI's APIKeyBase
        self.model: APIKey = APIKey(
            **{"in": APIKeyIn.header},
            name=TokenManager.header_key,
            description=self.__class__.__doc__,
        )
        self.scheme_name = self.__class__.__name__

        # This will be lazy loaded at the first request call
        self.manager = None

    async def __call__(self, request: Request) -> TokenPayload:
        """
        This method is called by FastAPI's dependency injection system when a TokenSecurity instance
        is injected to a route endpoint via the Depends() method. Lazily loads the OIDC config,
        the TokenDecoder, and the TokenManager if they are not already initialized.
        """
        if self.manager is None:
            loader = OpenidConfigLoader(self.domain, debug_logger=self.debug_logger)
            decoder = TokenDecoder(loader.jwks, self.algorithm, debug_logger=self.debug_logger)
            self.manager = TokenManager(
                loader.config,
                decoder,
                audience=self.audience,
                debug_logger=self.debug_logger,
            )

        try:
            token_payload = self.manager.extract_token_payload(request.headers)
        except Exception as err:
            if self.debug_exceptions:
                raise err
            else:
                raise HTTPException(
                    status_code=getattr(err, "status_code", status.HTTP_401_UNAUTHORIZED),
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        if not self.scopes:
            return token_payload

        missing_scopes = [s for s in self.scopes if s not in token_payload.permissions]
        if len(missing_scopes) > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token_payload
