import pendulum
import pytest
from plummet import frozen_time

from armasec_core.exceptions import AuthenticationError
from armasec_core.schemas.jwks import JWKs
from armasec_core.token_decoder import TokenDecoder
from armasec_core.token_manager import TokenManager


@pytest.fixture
def manager(rs256_openid_config, rs256_jwk):
    """
    This fixture provides a TokenManager configured with armasec's pytest_extension jwks and
    a token decoder using the same.
    """
    jwks = JWKs(keys=[rs256_jwk])
    decoder = TokenDecoder(jwks)
    return TokenManager(rs256_openid_config, decoder)


@frozen_time("2021-08-12 16:38:00")
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
    with pytest.raises(AuthenticationError, match="Invalid scheme format"):
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


@frozen_time("2021-09-16 20:56:00")
def test_extract_token_payload__success(manager, build_rs256_token):
    """
    This test verifies that the ``extract_token_payload()`` method successfully decodes a jwt and
    produces a TokenPayload instance from the contents.
    """
    exp = pendulum.parse("2021-09-17 20:56:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(sub="me", permissions=["read:all"], exp=exp.int_timestamp),
    )
    token_payload = manager.extract_token_payload({"Authorization": f"bearer {token}"})
    assert token_payload.sub == "me"
    assert token_payload.permissions == ["read:all"]
    assert token_payload.expire == exp


@frozen_time("2021-09-16 20:56:00")
def test_extract_token_payload__with_audience_succeeds(
    build_rs256_token, rs256_openid_config, rs256_jwk
):
    """
    This test verifies that the ``extract_token_payload()`` method successfully decodes a jwt that
    includes an audience claim when the TokenManager is initialized with an audience.
    """
    jwks = JWKs(keys=[rs256_jwk])
    decoder = TokenDecoder(jwks)
    manager = TokenManager(rs256_openid_config, decoder, audience="some-audience")
    exp = pendulum.parse("2021-09-17 20:56:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=exp.timestamp(),
            audience="some-audience",
        ),
    )
    token_payload = manager.extract_token_payload({"Authorization": f"bearer {token}"})
    assert token_payload.sub == "me"


@frozen_time("2021-09-16 20:56:00")
def test_extract_token_payload__fails_without_audience(
    build_rs256_token, rs256_openid_config, rs256_jwk
):
    """
    This test verifies that the ``extract_token_payload()`` method raises an exception when the
    jwt carries an audience claim and the TokenManager is not initialized with an audience.
    """
    jwks = JWKs(keys=[rs256_jwk])
    decoder = TokenDecoder(jwks)
    manager = TokenManager(rs256_openid_config, decoder)
    exp = pendulum.parse("2021-09-17 20:56:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=exp.timestamp(),
            aud="some-audience",
        ),
    )
    with pytest.raises(AuthenticationError):
        manager.extract_token_payload({"Authorization": f"bearer {token}"})


@frozen_time("2021-09-16 20:56:00")
def test_extract_token_payload__fails_with_bad_audience(
    build_rs256_token, rs256_openid_config, rs256_jwk
):
    """
    This test verifies that the ``extract_token_payload()`` method raises an exception when the
    jwt's audience does not match the audience of the TokenManager.
    """
    jwks = JWKs(keys=[rs256_jwk])
    decoder = TokenDecoder(jwks)
    manager = TokenManager(rs256_openid_config, decoder, audience="other-audience")
    exp = pendulum.parse("2021-09-17 20:56:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=exp.timestamp(),
            aud="some-audience",
        ),
    )
    with pytest.raises(AuthenticationError):
        manager.extract_token_payload({"Authorization": f"bearer {token}"})
