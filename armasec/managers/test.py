from typing import Optional, List

from jose import jwt

from armasec.managers.base import TokenManager
from armasec.token_payload import TokenPayload


class TestTokenManager(TokenManager):
    """
    This is a special TokenManager that can be used in tests to produce jwts or pack headers.
    """

    def encode_jwt(
        self,
        token_payload: TokenPayload,
        permissions_override: Optional[List[str]] = None,
        secret_override: Optional[str] = None,
    ):
        """
        Encodes a jwt based on a TokenPayload

        Adds any supplied scopes to a "permissions" claim in the jwt

        The ``secret_override`` parameter allows you to encode a jwt using a different secret. Any
        tokens produced in this way will not be decodable by this manager
        """
        claims = dict(
            **token_payload.to_dict(),
            iss=self.issuer,
            aud=self.audience,
        )
        if permissions_override is not None:
            claims["permissions"] = permissions_override
        return jwt.encode(
            claims,
            self.secret if not secret_override else secret_override,
            algorithm=self.algorithm,
        )

    def pack_header(self, *encode_jwt_args, **encode_jwt_kwargs):
        """
        Produces a header including a jwt that could be attached to a request.
        """
        token = self.encode_jwt(*encode_jwt_args, **encode_jwt_kwargs)
        return {self.header_key: f"{self.auth_scheme} {token}"}
