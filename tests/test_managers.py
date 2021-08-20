from datetime import datetime

import jose
import pytest

from armasec.exceptions import AuthenticationError
from armasec.token_payload import TokenPayload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
@pytest.mark.asyncio
async def test_decode__unpacks_a_jwt_into_a_token_payload(manager):
    original_payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token = manager.encode_jwt(original_payload)
    extracted_payload = await manager.decode(token)
    assert extracted_payload == original_payload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_unpack_token_from_header__extracts_a_token_from_a_request_header(manager):
    original_payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token = manager.encode_jwt(original_payload)
    assert (
        manager.unpack_token_from_header(
            {"Authorization": f"bearer {token}"},
        )
        == token
    )


def test_unpack_token_from_header__raises_exception_if_auth_header_not_found(manager):
    with pytest.raises(AuthenticationError, match="Could not find auth header"):
        manager.unpack_token_from_header(dict())


def test_unpack_token_from_header__raises_exception_if_no_scheme_prefix(manager):
    with pytest.raises(AuthenticationError, match="Could not extract scheme"):
        manager.unpack_token_from_header(dict(Authorization="xxxxxxxxxxxx"))


def test_unpack_token_from_header__raises_exception_if_no_token(manager):
    with pytest.raises(AuthenticationError, match="Could not extract scheme"):
        manager.unpack_token_from_header(dict(Authorization="bearer "))


def test_unpack_token_from_header__raises_exception_for_invalid_scheme(manager):
    with pytest.raises(AuthenticationError, match="Invalid auth scheme"):
        manager.unpack_token_from_header(dict(Authorization="carrier xxxxxxxxxxxx"))


@pytest.mark.freeze_time("2021-08-12 16:38:00")
@pytest.mark.asyncio
async def test_extract_token_payload__extracts_and_decodes_a_token_from_a_request_header(manager):
    original_payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token = manager.encode_jwt(original_payload)
    extracted_payload = await manager.extract_token_payload(
        {"Authorization": f"bearer {token}"},
    )
    assert extracted_payload == original_payload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_encode_jwt__creates_encoded_jwt_for_token(manager):
    """
    This test makes sure that the test_manager can encode a jwt correctly
    """
    token = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token_jwt = manager.encode_jwt(token)
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
def test_encode_jwt__permissions_override_can_set_different_permissions(manager):
    token = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token_jwt = manager.encode_jwt(token, permissions_override=[])
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
