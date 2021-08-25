from datetime import datetime

import jose
import pytest

from armasec.exceptions import AuthenticationError
from armasec.token_payload import TokenPayload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_decode__success(manager):
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
    extracted_payload = manager.decode(token)
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
def test_extract_token_payload__success(manager):
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
    extracted_payload = manager.extract_token_payload(
        {"Authorization": f"bearer {token}"},
    )
    assert extracted_payload == original_payload
