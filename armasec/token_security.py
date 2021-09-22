from typing import Iterable, Optional

from fastapi import HTTPException, status
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.api_key import APIKeyBase
from starlette.requests import Request

from armasec.token_manager import TokenManager
from armasec.token_payload import TokenPayload


class TokenSecurity(APIKeyBase):
    """
    An injectable Security class that returns a TokenPayload when used with Depends().
    """

    def __init__(
        self,
        manager: TokenManager,
        scopes: Optional[Iterable[str]] = None,
        debug: bool = False,
    ):
        self.manager = manager
        self.debug = debug
        self.model: APIKey = APIKey(
            **{"in": APIKeyIn.header},
            name=self.manager.header_key,
            description=self.__class__.__doc__,
        )
        self.scheme_name = self.__class__.__name__
        self.scopes = scopes

    async def __call__(self, request: Request) -> TokenPayload:
        """
        This method is called by FastAPI's dependency injection system when a TokenSecurity instance
        is injected to a route endpoint via the Depends() method.
        """
        try:
            token_payload = self.manager.extract_token_payload(request.headers)
        except Exception as err:
            if self.debug:
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
