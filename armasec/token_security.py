"""
This module defines a TokenSecurity injectable that can be used enforce access on FastAPI routes.
"""

from typing import Callable, Iterable, List, Optional

from auto_name_enum import AutoNameEnum, auto
from fastapi import HTTPException, status
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.security.api_key import APIKeyBase
from pydantic import ConfigDict, BaseModel
from snick import unwrap
from starlette.requests import Request

from armasec.exceptions import AuthenticationError, AuthorizationError
from armasec.openid_config_loader import OpenidConfigLoader
from armasec.pluggable import plugin_manager
from armasec.schemas import DomainConfig
from armasec.token_decoder import TokenDecoder
from armasec.token_manager import TokenManager
from armasec.token_payload import TokenPayload
from armasec.utilities import noop


class ManagerConfig(BaseModel):
    """
    Model class to represent a TokenManager instance and its domain configuration for easier mapping

    Attributes:
        manager: The TokenManager instance to use for decoding tokens.
        domain_config: The DomainConfig for the openid server.
    """

    manager: TokenManager
    domain_config: DomainConfig
    model_config = ConfigDict(arbitrary_types_allowed=True)


class PermissionMode(AutoNameEnum):
    """
    Endpoint permissions.

    Attributes:
        ALL:  Require all listed permissions.
        SOME: Require at least one of the listed permissions.
    """

    ALL = auto()
    SOME = auto()


class TokenSecurity(APIKeyBase):
    """
    An injectable Security class that returns a TokenPayload when used with Depends().

    Attributes:
        manager: The TokenManager to use for token validation and extraction.
    """

    manager: Optional[TokenManager]

    def __init__(
        self,
        domain_configs: List[DomainConfig],
        scopes: Optional[Iterable[str]] = None,
        permission_mode: PermissionMode = PermissionMode.ALL,
        debug_logger: Optional[Callable[..., None]] = None,
        debug_exceptions: bool = False,
        skip_plugins: bool = False,
    ):
        """
        Initializes the TokenSecurity instance.

        Args:
            domain_configs:   List of domain configuration to authenticate the tokens against.
            scopes:           Optional permissions scopes that should be checked
            permission_mode:  The PermissionMode to apply in the protected route.
            debug_logger:     A callable, that if provided, will allow debug logging. Should be
                              passed as a logger method like `logger.debug`
            debug_exceptions: If True, raise original exceptions. Should only be used in a testing
                              or debugging context.
            skip_plugins:     If True, do not evaluate plugin validators.
        """
        self.domain_configs = domain_configs
        self.scopes = scopes
        self.permission_mode = permission_mode

        self.debug_logger = debug_logger if debug_logger else noop
        self.debug_exceptions = debug_exceptions
        self.skip_plugins = skip_plugins

        # Settings needed for FastAPI's APIKeyBase
        self.model: APIKey = APIKey(
            **{"in": APIKeyIn.header},  # type: ignore[arg-type]
            name=TokenManager.header_key,
            description=self.__class__.__doc__,
        )
        self.scheme_name = self.__class__.__name__

        # This will be lazy loaded at the first request call
        self.managers: List[ManagerConfig] = list()

    async def __call__(self, request: Request) -> TokenPayload:
        """
        This method is called by FastAPI's dependency injection system when a TokenSecurity instance
        is injected to a route endpoint via the Depends() method. Lazily loads the OIDC config,
        the TokenDecoder, and the TokenManager if they are not already initialized.

        Args:
            request: The FastAPI request to check for secure access.
        """

        try:
            token_payload = self._extract_token_payload_from_manager(request)
        except AttributeError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as err:
            if self.debug_exceptions:
                raise err
            else:
                raise HTTPException(
                    status_code=getattr(err, "status_code", status.HTTP_401_UNAUTHORIZED),
                    detail=getattr(err, "detail", "Not authenticated"),
                    headers={"WWW-Authenticate": "Bearer"},
                )

        if self.scopes:
            token_permissions = set(token_payload.permissions)
            my_permissions = set(self.scopes)

            self.debug_logger(
                unwrap(
                    f"""
                    Checking my permissions {my_permissions} against token_permissions
                    {token_permissions} using PermissionMode {self.permission_mode}
                    """
                )
            )
            try:
                if self.permission_mode == PermissionMode.ALL:
                    message = unwrap(
                        f"""
                        Token permissions {token_permissions} missing some required permissions
                        {my_permissions - token_permissions}
                        """
                    )
                    AuthorizationError.require_condition(
                        my_permissions - token_permissions == set(),
                        message,
                    )
                elif self.permission_mode == PermissionMode.SOME:
                    message = unwrap(
                        f"""
                        Token permissions {token_permissions} missing at least
                        one required permissions
                        {my_permissions}
                        """
                    )
                    AuthorizationError.require_condition(
                        token_permissions & my_permissions,
                        message,
                    )
                else:
                    raise AuthorizationError(f"Unknown permission_mode: {self.permission_mode}")

            except Exception as err:
                if self.debug_exceptions:
                    raise err
                else:
                    raise HTTPException(
                        status_code=getattr(err, "status_code", status.HTTP_403_FORBIDDEN),
                        detail=getattr(err, "detail", "Not authorized"),
                        headers={"WWW-Authenticate": "Bearer"},
                    )

        if not self.skip_plugins:
            self.debug_logger("Applying plugin checks")
            try:
                plugin_manager.hook.armasec_plugin_check(
                    request=request,
                    token_payload=token_payload,
                    debug_logger=self.debug_logger,
                )
            except Exception as err:
                if self.debug_exceptions:
                    raise err
                else:
                    raise HTTPException(
                        status_code=getattr(err, "status_code", status.HTTP_403_FORBIDDEN),
                        detail=getattr(err, "detail", "Not authorized"),
                        headers={"WWW-Authenticate": "Bearer"},
                    )

        return token_payload

    def _load_all_managers(self) -> None:
        if len(self.managers) == 0:
            for domain_config in self.domain_configs:
                try:
                    manager = self._load_manager(domain_config)
                    self.managers.append(
                        ManagerConfig(manager=manager, domain_config=domain_config)
                    )
                except AuthenticationError:
                    self.debug_logger(f"Failed to match JWK against domain {domain_config.domain}")
                except Exception as err:
                    if self.debug_exceptions:
                        self.debug_logger(f"Exception caught: {err.__class__.__name__}")

        AuthenticationError.require_condition(
            len(self.managers) > 0,
            "Not authenticated: couldn't load any TokenManager instance",
        )

    def _load_manager(self, domain_config: DomainConfig) -> TokenManager:
        self.debug_logger(f"Lazy loading TokenManager for domain {domain_config.domain}")
        loader = OpenidConfigLoader(
            domain_config.domain, use_https=domain_config.use_https, debug_logger=self.debug_logger
        )
        decoder = TokenDecoder(
            loader.jwks,
            domain_config.algorithm,
            debug_logger=self.debug_logger,
            payload_claim_mapping=domain_config.payload_claim_mapping,
        )
        return TokenManager(
            loader.config,
            decoder,
            audience=domain_config.audience,
            debug_logger=self.debug_logger,
        )

    def _extract_token_payload_from_manager(self, request: Request) -> TokenPayload:
        token_payload = None

        self._load_all_managers()

        for manager_config in self.managers:
            try:
                token_payload = manager_config.manager.extract_token_payload(request.headers)
            except Exception as err:
                self.debug_logger(f"Exception caught: {err.__class__.__name__}")
            else:
                AuthenticationError.require_condition(
                    token_payload is not None,
                    "Not authenticated: could not find matching JWK"
                    " with any input domain or token is malformed",
                )
                message = "Not authorized: token doesn't contain necessary key-value pairs"
                for key_to_match, value_to_match in manager_config.domain_config.match_keys.items():
                    if isinstance(value_to_match, bool):
                        AuthorizationError.require_condition(
                            getattr(token_payload, key_to_match) is value_to_match, message
                        )
                    elif isinstance(value_to_match, (str, int, float)):
                        AuthorizationError.require_condition(
                            getattr(token_payload, key_to_match) == value_to_match,
                            message,
                        )
                    else:
                        AuthorizationError.require_condition(
                            set(getattr(token_payload, key_to_match)) & set(value_to_match),
                            message,
                        )
                break

        # make static type analyzer happy :)
        assert token_payload is not None

        return token_payload
