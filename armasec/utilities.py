"""
Provides some utility functions predominately intended to be used in testing
"""
from typing import List, Optional

from jose import jwt

from armasec.managers.base import TokenManager
from armasec.token_payload import TokenPayload


def encode_jwt(
    manager: TokenManager,
    token_payload: TokenPayload,
    permissions_override: Optional[List[str]] = None,
    secret_override: Optional[str] = None,
):
    """
    Uses a TokenManager to encodes a jwt based on a TokenPayload.

    Adds any supplied scopes to a "permissions" claim in the jwt.

    The ``secret_override`` parameter allows you to encode a jwt using a different secret. Any
    tokens produced in this way will not be decodable by the supplied manager.
    """
    claims = dict(
        **token_payload.to_dict(),
        iss=manager.issuer,
        aud=manager.audience,
    )
    if permissions_override is not None:
        claims["permissions"] = permissions_override
    return jwt.encode(
        claims,
        manager.secret if not secret_override else secret_override,
        algorithm=manager.algorithm,
    )


def pack_header(
    manager: TokenManager,
    *encode_jwt_args,
    **encode_jwt_kwargs,
):
    """
    Uses a TokenManager to produces a header including a jwt that could be attached to a request.
    """
    token = encode_jwt(manager, *encode_jwt_args, **encode_jwt_kwargs)
    return {manager.header_key: f"{manager.auth_scheme} {token}"}
