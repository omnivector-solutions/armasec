"""
This module defines the core Armasec class.
"""

from functools import lru_cache
from typing import Callable, List, Optional

from fastapi import HTTPException, status

from armasec.schemas import DomainConfig
from armasec.token_security import PermissionMode, TokenSecurity
from armasec.utilities import noop


class Armasec:
    """
    This is a factory class for TokenSecurity. It allows the machinery of armasec to be initialized
    correctly so that the factory method `lockdown` can initialize new instances of TokenSecurity
    to protect routes. It's not essential to use Armasec to secure routes, but it cuts down on the
    boilerplate necessary to do so.
    """

    def __init__(
        self,
        domain_configs: Optional[List[DomainConfig]] = None,
        debug_logger: Optional[Callable[[str], None]] = noop,
        debug_exceptions: bool = False,
        **kargs,
    ):
        """
        Stores initialization values for the TokenSecurity. All are passed through.

        Args:
            domain_configs:   List of domain configuration to authenticate the tokens against.
            debug_logger:     A callable, that if provided, will allow debug logging. Should be
                              passed as a logger method like `logger.debug`
            debug_exceptions: If True, raise original exceptions. Should only be used in a testing
                              or debugging context.
            kargs:            Arguments compatible to instantiate the DomainConfig model.
        """
        primary_domain_config = DomainConfig(**kargs)
        if primary_domain_config.domain:
            self.domain_configs = [primary_domain_config]
        elif domain_configs is not None:
            self.domain_configs = domain_configs
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No domain was input.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        self.debug_logger = debug_logger
        self.debug_exceptions = debug_exceptions

    @lru_cache(maxsize=128)
    def lockdown(
        self,
        *scopes: str,
        permission_mode: PermissionMode = PermissionMode.ALL,
        skip_plugins: bool = False,
    ) -> TokenSecurity:
        """
        Initialize an instance of TokenSecurity to lockdown a route. Uses memoization to minimize
        the number of TokenSecurity instances initialized. Applies supplied permission_mode when
        checking token permssions against TokenSecurity scopes.

        Args:
            scopes: A list of scopes needed to access the endpoint.
            permissions_mode: If "ALL", all scopes listed are required for access. If "SOME", only
                one of the scopes listed are required for access.
            skip_plugins: If True, do not evaluate plugin validators.
        """
        return TokenSecurity(
            domain_configs=self.domain_configs,
            scopes=scopes,
            permission_mode=permission_mode,
            debug_logger=self.debug_logger,
            debug_exceptions=self.debug_exceptions,
            skip_plugins=skip_plugins,
        )

    def lockdown_all(
        self,
        *scopes: str,
        skip_plugins: bool = False,
    ) -> TokenSecurity:
        """
        Initialize an instance of TokenSecurity to lockdown a route. Uses memoization to minimize
        the number of TokenSecurity instances initialized. Requires all the scopes in the
        TokenSecurity instance to be included in the token permissions. This is just a wrapper
        around `lockdown()` with default permission_mode and is only included for symmetry.

        Args:
            scopes: A list of the scopes needed to access the endpoint. All are required.
            skip_plugins: If True, do not evaluate plugin validators.
        """
        return self.lockdown(
            *scopes,
            permission_mode=PermissionMode.ALL,
            skip_plugins=skip_plugins,
        )

    def lockdown_some(
        self,
        *scopes: str,
        skip_plugins: bool = False,
    ) -> TokenSecurity:
        """
        Initialize an instance of TokenSecurity to lockdown a route. Uses memoization to minimize
        the number of TokenSecurity instances initialized. Requires at least one permission in the
        token to match a scope attached to the TokenSecurity instance.

        Args:
            scopes: A list of the scopes needed to access the endpoint. Only one is required.
            skip_plugins: If True, do not evaluate plugin validators.
        """
        return self.lockdown(
            *scopes,
            permission_mode=PermissionMode.SOME,
            skip_plugins=skip_plugins,
        )
