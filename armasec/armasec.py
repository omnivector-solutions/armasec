"""
This module defines the core Armasec class.
"""

from functools import lru_cache
from typing import Callable, Optional

from armasec.token_security import TokenSecurity
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
        domain: str,
        audience: Optional[str] = None,
        algorithm: str = "RS256",
        debug_logger: Optional[Callable[[str], None]] = noop,
        debug_exceptions: bool = False,
    ):
        """
        Stores initialization values for the TokenSecurity. All are passed through.

        Args:
            domain:           The OIDC domain where resources are loaded
            audience:         Optional designation of the token audience.
            algorithm:        The the algorithm to use for decoding. Defaults to RS256.
            debug_logger:     A callable, that if provided, will allow debug logging. Should be
                              passed as a logger method like `logger.debug`
            debug_exceptions: If True, raise original exceptions. Should only be used in a testing
                              or debugging context.
        """
        self.domain = domain
        self.audience = audience
        self.algorithm = algorithm
        self.debug_logger = debug_logger
        self.debug_exceptions = debug_exceptions

    @lru_cache(maxsize=128)
    def lockdown(self, *scopes: str) -> TokenSecurity:
        """
        Initialize an instance of TokenSecurity to lockdown a route. Uses memoization to minimize
        the number of TokenSecurity instances initialized.
        """
        return TokenSecurity(
            self.domain,
            audience=self.audience,
            algorithm=self.algorithm,
            scopes=scopes,
            debug_logger=self.debug_logger,
            debug_exceptions=self.debug_exceptions,
        )
