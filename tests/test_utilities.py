from datetime import datetime

import jose
import pytest

from armasec.token_payload import TokenPayload
from armasec.utilities import encode_jwt


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_encode_jwt__success(manager):
    """
    This test ensures that the TestTokenManager can create a properly encoded jwt from a
    TokenPayload instance.
    """
    token = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token_jwt = encode_jwt(manager, token)
    payload = jose.jwt.decode(
        token_jwt,
        "itsasecrettoeverybody",
        algorithms=["HS256"],
        issuer=manager.issuer,
        audience=manager.audience,
    )
    assert payload["sub"] == "someone"
    assert payload["permissions"] == ["a", "b", "c"]
    assert payload["exp"] == int(datetime.utcnow().timestamp())


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_encode_jwt__permissions_override(manager):
    """
    This test ensures that the TestTokenManager can encode a jwt from a TokenPayload instance with
    the permissions list overridden by the ``permissions_override`` parameter.
    """
    token = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token_jwt = encode_jwt(manager, token, permissions_override=[])
    payload = jose.jwt.decode(
        token_jwt,
        "itsasecrettoeverybody",
        algorithms=["HS256"],
        issuer=manager.issuer,
        audience=manager.audience,
    )
    assert payload["sub"] == "someone"
    assert payload["permissions"] == []
    assert payload["exp"] == int(datetime.utcnow().timestamp())
