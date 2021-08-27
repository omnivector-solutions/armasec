from typing import List

import httpx
import snick
from jose import jwt, jwk
from starlette.status import HTTP_200_OK

from armasec.managers.base import TokenManager
from armasec.exceptions import AuthenticationError
from armasec.jwk import JWK


class AsymmetricManager(TokenManager):
    """
    Provides a TokenManager that retrieves JWKs from an OIDC provider to use asymmetric signature
    validation algorithms during the `decode()` process
    """

    jwks: List[JWK]

    def __init__(
        self,
        secret: str,
        algorithm: str,
        client_id: str,
        domain: str,
        audience: str,
        *args,
        **kwargs,
    ):
        issuer = f"https://{domain}/"
        super().__init__(secret, algorithm, issuer, audience, **kwargs)
        self.client_id = client_id
        self.domain = domain
        self.load_jwks()

    def load_jwks(self):
        """
        Retrives JWKs public keys from an OIDC provider. Verifies that the keys may be retrieved,
        checks that they are wellformed, and deserializes them into list of JWK instances.
        """

        jwks_url = f"https://{self.domain}/.well-known/jwks.json"
        self.debug_logger(f"Attempting to fetch jwks from '{jwks_url}'")
        with AuthenticationError.handle_errors(
            message=f"Call to {jwks_url=} failed",
            do_except=self.log_error,
        ):
            response = httpx.get(jwks_url)
        AuthenticationError.require_condition(
            response.status_code == HTTP_200_OK,
            f"Didn't get a success status code from {jwks_url=}: {response.status_code=}",
        )
        data = response.json()
        AuthenticationError.require_condition(
            'keys' in data,
            "Response jwks data is malformed",
        )
        self.jwks = [JWK(**k) for k in data["keys"]]

    def _decode_to_payload_dict(self, token: str) -> dict:
        """
        Overload for the base class method. Searches for a public keys within the JWKs that matches
        the incoming token's unverified header and uses it to verify and decode the payload. If a
        matching public key cannot be found, it will raise an AuthenticationError.
        """
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        AuthenticationError.require_condition(
           kid,
            f"Unverified header doesn't contain 'kid'...not sure how this happened",
        )
        self.debug_logger(f"Extraced unverified header: {unverified_header}")

        for jwk in self.jwks:
            self.debug_logger(f"Checking key in jwk: {jwk}")
            if jwk.kid == kid:
                self.debug_logger("Key matches unverified header. Decoding token...")
                return dict(
                    jwt.decode(
                        token,
                        jwk,
                        algorithms=[self.algorithm],
                        audience=self.audience,
                        issuer=self.issuer,
                    )
                )

        raise AuthenticationError("Could not find a matching jwk")
