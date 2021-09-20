"""
This module defines the core Armasec class.
"""

from functools import lru_cache

from armasec.openid_config_loader import OpenidConfigLoader
from armasec.token_decoders.rs256 import RS256Decoder
from armasec.token_manager import TokenManager
from armasec.token_security import TokenSecurity
from armasec.utilities import noop


class Armasec:
    """
    This is the core class of the armasec package.  It pulls all the components together to allow
    you to secure your endpoints with a simple call to `lockdown`.

    Technically, it is a factory class for instances of TokenSecurity.
    """

    def __init__(self, domain, audience=None, decoder_class=RS256Decoder, debug_logger=noop):
        """
        Initializes the armasec security factory.

        Args:
            domain:        The OIDC domain where resources are loaded
            audience:      Optional designation of the token audience.
            decoder_class: The decoder that should be used to verify and extract jwts.
            debug_logger:  A callable, that if provided, will allow debug logging. Should be passed
                           as a logger method like `logger.debug`
        """
        self.domain = domain
        self.audience = audience
        self.decoder_class = decoder_class
        self.debug_logger = debug_logger

        self.loader = OpenidConfigLoader(self.domain, debug_logger=self.debug_logger)
        self.decoder = decoder_class(self.loader.jwks, debug_logger=self.debug_logger)
        self.manager = TokenManager(
            self.loader.config,
            self.decoder,
            audience=self.audience,
            debug_logger=self.debug_logger,
        )

    @lru_cache
    def lockdown(self, *scopes: str) -> TokenSecurity:
        """
        Produce an instance of TokenSecurity initialized with the provided scopes. Memoized to avoid
        redundant initialization.
        """
        return TokenSecurity(self.manager, scopes=scopes)
