"""
This module provides an abstract base class for algorithmic token decoders
"""

from __future__ import annotations

from functools import partial
from typing import Callable

from jose import jwt

from armasec.exceptions import AuthenticationError, PayloadMappingError
from armasec.schemas.jwks import JWKs
from armasec.token_payload import TokenPayload
from armasec.utilities import log_error, noop


class TokenDecoder:
    """
    Decoder class used to decode tokens given an algorithm and jwks.
    """

    algorithm: str

    def __init__(
        self,
        jwks: JWKs,
        algorithm: str = "RS256",
        debug_logger: Callable[..., None] | None = None,
        decode_options_override: dict | None = None,
        permission_extractor: Callable[[dict], list[str]] | None = None,
    ):
        """
        Initializes a TokenDecoder.

        Args:
            algorithm:               The algorithm to use for decoding. Defaults to RS256.
            jwks:                    JSON web keys object holding the public keys for decoding.
            openid_config:           The openid_configuration needed for claims such as 'issuer'.
            debug_logger:            A callable, that if provided, will allow debug logging. Should
                                     be passed as a logger method like `logger.debug`
            decode_options_override: Options that can override the default behavior of the jwt
                                     decode method. For example, one can ignore token expiration by
                                     setting this to `{ "verify_exp": False }`
            permission_extractor:    Optional function that may be used to extract permissions from
                                     the decoded token dictionary when the permissions are not a
                                     top-level claim in the token. If not provided, permissions will
                                     be assumed to be a top-level claim in the token.

                                     Consider the example token:

                                     ```
                                     {
                                       "exp": 1728627701,
                                       "iat": 1728626801,
                                       "jti": "24fdb7ef-d773-4e6b-982a-b8126dd58af7",
                                       "sub": "dfa64115-40b5-46ab-924c-c376e73f631d",
                                       "azp": "my-client",
                                       "resource_access": {
                                         "my-client": {
                                           "roles": [
                                             "read:stuff"
                                           ]
                                         },
                                       },
                                     }
                                     ```

                                     In this example, the permissions are found at
                                     `resource_access.my-client.roles`. To produce a TokenPayload
                                     with the permissions set as expected, you could supply a
                                     permission extractor like this:

                                     ```
                                     def my_extractor(decoded_token: dict) -> list[str]:
                                         resource_key = decoded_token["azp"]
                                         return decoded_token["resource_access"][resource_key]["roles"]
                                     ```
        """
        self.algorithm = algorithm
        self.jwks = jwks
        self.debug_logger = debug_logger if debug_logger else noop
        self.decode_options_override = decode_options_override if decode_options_override else {}
        self.permission_extractor = permission_extractor

    def get_decode_key(self, token: str) -> dict:
        """
        Search for a public keys within the JWKs that matches the incoming token.

        Compares the token's unverified header against available JWKs. Uses the matching JWK for the
        decode key.  Raise AuthenticationError if matching public key cannot be found.

        Args:
            token: The token to match against available JWKs.
        """
        self.debug_logger("Getting decode key from JWKs")
        unverified_header = jwt.get_unverified_header(token)
        self.debug_logger(f"Extraced unverified header: {unverified_header}")
        kid = unverified_header.get("kid")
        AuthenticationError.require_condition(
            kid,
            "Unverified header doesn't contain 'kid'...not sure how this happened",
        )

        for jwk in self.jwks.keys:
            self.debug_logger(f"Checking key in jwk: {jwk}")
            if jwk.kid == kid:
                self.debug_logger("Key matches unverified header. Using as decode secret.")
                return jwk.model_dump()

        raise AuthenticationError("Could not find a matching jwk")

    def decode(self, token: str, **claims) -> TokenPayload:
        """
        Decode a JWT into a TokenPayload while checking signatures and claims.

        Args:
            token:  The token to decode.
            claims: Additional claims to verify in the token.
        """
        self.debug_logger(f"Attempting to decode '{token}'")
        self.debug_logger(f"  checking claims: {claims}")
        with AuthenticationError.handle_errors(
            "Failed to decode token string",
            do_except=partial(log_error, self.debug_logger),
        ):
            payload_dict = dict(
                jwt.decode(
                    token,
                    self.get_decode_key(token),
                    algorithms=[self.algorithm],
                    options=self.decode_options_override,
                    **claims,
                )
            )
            self.debug_logger(f"Raw payload dictionary is {payload_dict}")

        with PayloadMappingError.handle_errors(
            "Failed to map decoded token to TokenPayload",
            do_except=partial(log_error, self.debug_logger),
        ):
            if self.permission_extractor is not None:
                self.debug_logger("Attempting to extract permissions.")
                payload_dict["permissions"] = self.permission_extractor(payload_dict)
                self.debug_logger(
                    f"Payload dictionary with extracted permissions is {payload_dict}"
                )

            self.debug_logger("Attempting to convert to TokenPayload")
            token_payload = TokenPayload(
                **payload_dict,
                original_token=token,
            )
            self.debug_logger(f"Built token_payload as {token_payload}")
            return token_payload


def extract_keycloak_permissions(decoded_token: dict) -> list[str]:
    """
    Provide a permission extractor for Keycloak.

    By default, Keycloak packages the roles for a given client
    nested within the "resource_access" claim. In order to extract
    those roles into the expected permissions in the TokenPayload,
    this permission_extractor can be used.

    Here is an example decoded token from Keycloak (with some stuff
    removed to improve readability):

    ```
    {
      "exp": 1728627701,
      "iat": 1728626801,
      "jti": "24fdb7ef-d773-4e6b-982a-b8126dd58af7",
      "sub": "dfa64115-40b5-46ab-924c-c376e73f631d",
      "azp": "my-client",
      "resource_access": {
        "my-client": {
          "roles": [
            "read:stuff"
          ]
        },
      },
    }
    ```

    This extractor would extract the roles `["read:stuff"]` as the
    permissions for the TokenPayload returned by the TokenDecoder.
    """
    resource_key = decoded_token["azp"]
    return decoded_token["resource_access"][resource_key]["roles"]
