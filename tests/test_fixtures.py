from datetime import datetime

import jose
import pytest

from armasec.token_payload import TokenPayload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_encode_jwt__creates_encoded_jwt_for_token(manager, encode_jwt):
    token = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token_jwt = encode_jwt(token)
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
