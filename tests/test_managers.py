from datetime import datetime

import jose
import pytest

from armasec.exceptions import AuthenticationError
from armasec.token_payload import TokenPayload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
@pytest.mark.asyncio
async def test_decode__success(manager):
    """
    This test verifies that the ``decode()`` method can successfully unpack a valid jwt into a dict
    containing the payload elements.
    """
    original_payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token = manager.encode_jwt(original_payload)
    extracted_payload = await manager.decode(token)
    assert extracted_payload == original_payload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_unpack_token_from_header__success(manager):
    """
    This test verifies that the ``unpack_token_from_header()`` method can successfully unpack a jwt
    from a header mapping where it is embedded with a scheme marker (like 'bearer').
    """
    original_payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    token = manager.encode_jwt(original_payload)
    unpacked_token = manager.unpack_token_from_header({"Authorization": f"bearer {token}"})
    assert token == unpacked_token


def test_unpack_token_from_header__fail_when_auth_header_not_found(manager):
    """
    This test ensures that ``unpack_token_from_header()`` raises an AuthenticationError when an auth
    header is not found in header dict.
    """
    with pytest.raises(AuthenticationError, match="Could not find auth header"):
        manager.unpack_token_from_header(dict())


def test_unpack_token_from_header__fail_on_no_scheme_prefix(manager):
    """
    This test ensures that ``unpack_token_from_header()`` raises an AuthenciationError when an auth
    header lacks the correct scheme prefix before the jwt.
    """
    with pytest.raises(AuthenticationError, match="Could not extract scheme"):
        manager.unpack_token_from_header(dict(Authorization="xxxxxxxxxxxx"))


def test_unpack_token_from_header__fail_when_no_token(manager):
    """
    This test ensures that ``unpack_token_from_header()`` raises an AuthenciationError when an auth
    header lacks the embedded jwt.
    """
    with pytest.raises(AuthenticationError, match="Could not extract scheme"):
        manager.unpack_token_from_header(dict(Authorization="bearer "))


def test_unpack_token_from_header__fail_for_invalid_scheme(manager):
    """
    This  test ensures that ``unpack_token_from_header()`` raises an AutenticationError when an auth
    header lacks a maching scheme.
    """
    with pytest.raises(AuthenticationError, match="Invalid auth scheme"):
        manager.unpack_token_from_header(dict(Authorization="carrier xxxxxxxxxxxx"))


@pytest.mark.freeze_time("2021-08-12 16:38:00")
@pytest.mark.asyncio
async def test_extract_token_payload__success(manager):
    """
    This test verifies that the ``extract_token_payload()`` method successfully decodes a jwt and
    produces a TokenPayload instance from the contents.
    """
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
def test_encode_jwt__success(manager):
    """
    This test ensures that the TestTokenManager can create a properly encoded  jwt from a
    TokenPayload instance.
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
