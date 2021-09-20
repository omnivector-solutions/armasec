"""
This module provides the OpenidConfigLoader which is used to load openid-configuration data from an
OIDC provider.
"""
from functools import partial
from typing import Callable, Optional

import httpx
import starlette

from armasec.exceptions import AuthenticationError
from armasec.schemas.jwks import JWKs
from armasec.schemas.openid_config import OpenidConfig
from armasec.utilities import log_error, noop


class OpenidConfigLoader:
    _config: Optional[OpenidConfig] = None
    _jwks: Optional[JWKs] = None

    def __init__(self, domain: str, debug_logger: Optional[Callable[..., None]] = None):
        """
        Initializes a base TokenManager.

        Args:

            secret:                  The secret key needed to decode a token
            domain:                  The domain of the OIDC provider. This is to construct the
                                     openid-configuration url
            debug_logger:            A callable, that if provided, will allow debug logging. Should
                                     be passed as a logger method like `logger.debug`
        """
        self.domain = domain
        self.debug_logger = debug_logger if debug_logger else noop

    @staticmethod
    def build_openid_config_url(domain):
        """
        Builds a url for an openid configuration given a domain.
        """
        return f"https://{domain}/.well-known/openid-configuration"

    def _load_openid_resource(self, url: str):
        """
        Helper method to load data from an openid connect resource.
        """
        self.debug_logger(f"Attempting to fetch from openid resource '{url}'")
        with AuthenticationError.handle_errors(
            message=f"Call to url {url} failed",
            do_except=partial(log_error, self.debug_logger),
        ):
            response = httpx.get(url)
        AuthenticationError.require_condition(
            response.status_code == starlette.status.HTTP_200_OK,
            f"Didn't get a success status code from url {url}: {response.status_code}",
        )
        return response.json()

    @property
    def config(self) -> OpenidConfig:
        """
        Retrive the openid config from an OIDC provider. Lazy loads the config so that API calls are
        deferred until the coniguration is needed.
        """
        if not self._config:
            self.debug_logger("Fetching openid configration")
            data = self._load_openid_resource(self.build_openid_config_url(self.domain))
            with AuthenticationError.handle_errors(
                message="openid config data was invalid",
                do_except=partial(log_error, self.debug_logger),
            ):
                self._config = OpenidConfig(**data)

        return self._config

    @property
    def jwks(self) -> JWKs:
        """
        Retrives JWKs public keys from an OIDC provider. Lazy loads the jwks so that API calls are
        deferred until the jwks are needed.
        """
        if not self._jwks:
            self.debug_logger("Fetching jwks")
            data = self._load_openid_resource(self.config.jwks_uri)
            with AuthenticationError.handle_errors(
                message="jwks data was invalid",
                do_except=partial(log_error, self.debug_logger),
            ):
                self._jwks = JWKs(**data)

        return self._jwks
