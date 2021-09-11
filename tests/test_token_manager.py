from datetime import datetime, timezone

import pytest

from armasec.exceptions import AuthenticationError
from armasec.schemas.jwks import JWKs
from armasec.token_decoders.rs256 import RS256Decoder
from armasec.token_manager import TokenManager


@pytest.fixture
def manager(rs256_openid_config, rs256_jwk):
    """
    This fixture provides a TokenManager configured with armasec's pytest_extension jwks and
    a token decoder using the same.
    """
    jwks = JWKs(keys=[rs256_jwk])
    decoder = RS256Decoder(jwks)
    return TokenManager(rs256_openid_config, decoder)


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_unpack_token_from_header__success(manager):
    """
    This test verifies that the ``unpack_token_from_header()`` method can successfully unpack a jwt
    from a header mapping where it is embedded with a scheme marker (like 'bearer').
    """
    headers = {"Authorization": "bearer dummy-token"}
    assert manager.unpack_token_from_header(headers) == "dummy-token"


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


@pytest.mark.freeze_time("2021-09-16 20:56:00")
def test_extract_token_payload__success(manager, build_rs256_token):
    """
    This test verifies that the ``extract_token_payload()`` method successfully decodes a jwt and
    produces a TokenPayload instance from the contents.
    """
    exp = datetime(2021, 9, 17, 20, 56, 0, tzinfo=timezone.utc)
    token = build_rs256_token(
        claim_overrides=dict(sub="me", permissions=["read:all"], exp=exp.timestamp()),
    )
    token_payload = manager.extract_token_payload({"Authorization": f"bearer {token}"})
    assert token_payload.sub == "me"
    assert token_payload.permissions == ["read:all"]
    assert token_payload.expire == exp
