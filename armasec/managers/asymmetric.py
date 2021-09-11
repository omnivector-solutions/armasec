"""
This module provides a TokenManager that is designed to use with OpenID issued tokens that are
asymmetrically signed.
"""
from typing import List, Optional

import httpx
import snick
from jose import jwt
from starlette.status import HTTP_200_OK

from armasec.exceptions import AuthenticationError
from armasec.openid_config import OpenidConfig
from armasec.jwks import JWK
from armasec.managers.base import TokenManager
from armasec.utilities import build_openid_config_url


class AsymmetricManager(TokenManager):
    """
    Provides a TokenManager that retrieves JWKs from an OIDC provider to use asymmetric signature
    validation algorithms during the `decode()` process.
    """

    jwks: List[JWK]

    def __init__(
        self,
        secret: str,
        algorithm: str,
        client_id: str,
        domain: str,
        audience: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(
            secret,
            algorithm,
            audience=audience,
            **kwargs,
        )
        self.client_id = client_id
        self.domain = domain
        self.debug_logger(
            snick.dedent(
                f"""
                Additionally initialized {self.__class__.__name__} with:
                    client_id: {self.client_id}
                    domain: {self.domain}
                """
            )
        )
        self.openid_config = self.fetch_openid_config()
        self.issuer = self.openid_config.issuer
        self.jwks = self.fetch_jwks()

    def _load_openid_resource(self, url: str):
        """
        Helper method to load data from an openid connect resource.
        """
        self.debug_logger(f"Attempting to fetch from openid resource '{url}'")
        with AuthenticationError.handle_errors(
            message=f"Call to url {url} failed",
            do_except=self.log_error,
        ):
            response = httpx.get(url)
        AuthenticationError.require_condition(
            response.status_code == HTTP_200_OK,
            f"Didn't get a success status code from url {url}: {response.status_code}",
        )
        return response.json()

    def fetch_openid_config(self) -> OpenidConfig:
        """
        Retrives the openid config from an OIDC provider.
        """
        self.debug_logger(f"Fetching openid configration")
        data = self._load_openid_resource(build_openid_config_url(self.domain))
        AuthenticationError.require_condition(
            "issuer" in data,
            "openid configuration didn't include an 'issuer'",
        )
        with AuthenticationError.handle_errors(
            message="openid config data was invalid",
            do_except=self.log_error,
        ):
            return OpenidConfig(**data)

    def fetch_jwks(self) -> List[JWK]:
        """
        Retrives JWKs public keys from an OIDC provider. Verifies that the keys may be retrieved,
        checks that they are wellformed, and deserializes them into list of JWK instances.
        """
        self.debug_logger(f"Fetching jwks")
        data = self._load_openid_resource(self.openid_config.jwks_uri)
        AuthenticationError.require_condition(
            "keys" in data,
            "Response jwks data is malformed",
        )
        with AuthenticationError.handle_errors(
            message="jwks data was invalid",
            do_except=self.log_error,
        ):
            return [JWK(**k) for k in data["keys"]]

    def _decode_to_payload_dict(self, token: str) -> dict:
        """
        Overload for the base class method. Searches for a public keys within the JWKs that matches
        the incoming token's unverified header and uses it to vekrify and decode the payload. If a
        matching public key cannot be found, it will raise an AuthenticationError.
        """
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        AuthenticationError.require_condition(
            kid,
            "Unverified header doesn't contain 'kid'...not sure how this happened",
        )
        self.debug_logger(f"Extraced unverified header: {unverified_header}")

        for jwk in self.jwks:
            self.debug_logger(f"Checking key in jwk: {jwk}")
            if jwk.kid == kid:
                self.debug_logger("Key matches unverified header. Decoding token...")
                return dict(
                    jwt.decode(
                        token,
                        jwk.dict(),
                        algorithms=[self.algorithm],
                        audience=self.audience,
                        issuer=self.issuer,
                    )
                )

        raise AuthenticationError("Could not find a matching jwk")
