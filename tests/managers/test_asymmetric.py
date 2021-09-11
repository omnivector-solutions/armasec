from unittest import mock

import httpx
import pytest
import starlette

from armasec.exceptions import AuthenticationError
from armasec.managers import AsymmetricManager


def test_init__success(mock_openid_server):
    """
    This test verifies that an AssymmetricManager can be propery constructed. It also check to make
    sure that calls are made to the OIDC openid-configuration and jwks endpoints
    """
    AsymmetricManager(
        secret=mock_openid_server.client_secret,
        client_id=mock_openid_server.client_id,
        algorithm=mock_openid_server.algorithm,
        domain=mock_openid_server.domain,
    )
    assert mock_openid_server.openid_config_route.called
    assert mock_openid_server.jwks_route.called


def test_init__fails_if_request_for_jwks_fails(mock_openid_server):
    """
    This test verifies the call to an OIDC's jwks endpoint does not raise an exception and that
    raised exceptions are wrapped with a meaningful error.
    """
    with pytest.raises(AuthenticationError, match="Call to .* failed"):
        mock_openid_server.jwks_route.side_effect = Exception("Boom")
        AsymmetricManager(
            secret=mock_openid_server.client_secret,
            client_id=mock_openid_server.client_id,
            algorithm=mock_openid_server.algorithm,
            domain=mock_openid_server.domain,
        )


def test_init__fails_if_request_for_jwks_response_status_is_not_OK(mock_openid_server):
    """
    This test verifies that the call to an OIDC's jwks endpoint results in an OK status code and
    other codes result in an exception being raised.
    """
    with pytest.raises(AuthenticationError, match="Didn't get a success status code"):
        mock_openid_server.jwks_route.return_value = httpx.Response(
            starlette.status.HTTP_400_BAD_REQUEST,
        )
        AsymmetricManager(
            secret=mock_openid_server.client_secret,
            client_id=mock_openid_server.client_id,
            algorithm=mock_openid_server.algorithm,
            domain=mock_openid_server.domain,
        )


def test_init__fails_if_response_is_malformed(mock_openid_server):
    """
    This test verifies that a the data returned by an OIDC's jwks endpoint is formed as
    expected with a "key" element, and that if the data is malformed, a exception is raised.
    """
    with pytest.raises(AuthenticationError, match="Response jwks data is malformed"):
        mock_openid_server.jwks_route.return_value = httpx.Response(
            starlette.status.HTTP_200_OK,
            json=dict(garbage="data"),
        )
        AsymmetricManager(
            secret=mock_openid_server.client_secret,
            client_id=mock_openid_server.client_id,
            algorithm=mock_openid_server.algorithm,
            domain=mock_openid_server.domain,
        )


def test__decode_to_payload_dict__success(mock_openid_server):
    """
    This test verifies that a the _decode_to_payload_dict() method can successfully extract a
    token payload when it finds a matching public key in the JWKs.
    """
    manager = AsymmetricManager(
        secret=mock_openid_server.client_secret,
        client_id=mock_openid_server.client_id,
        algorithm=mock_openid_server.algorithm,
        domain=mock_openid_server.domain,
        audience=mock_openid_server.audience,
    )
    payload = manager._decode_to_payload_dict(mock_openid_server.access_token)
    assert payload["iss"] == mock_openid_server.openid_config.issuer


def test__decode_to_payload_dict__fails_if_kid_not_in_unverified_header(mock_openid_server):
    """
    This test verifies that an exception is raised if the token's unverified header does not contain
    a "kid" claim.
    """
    manager = AsymmetricManager(
        secret=mock_openid_server.client_secret,
        client_id=mock_openid_server.client_id,
        algorithm=mock_openid_server.algorithm,
        domain=mock_openid_server.domain,
        audience=mock_openid_server.audience,
    )
    with mock.patch("jose.jwt.get_unverified_header", return_value=dict()):
        with pytest.raises(AuthenticationError, match="doesn't contain 'kid'"):
            manager._decode_to_payload_dict(mock_openid_server.access_token)


def test__decode_to_payload_dict__fails_if_no_jwk_matches_unverified_header(mock_openid_server):
    """
    This test verifies that an exception is raised if none of the loaded JWKs match the token's
    unverified header.
    """
    manager = AsymmetricManager(
        secret=mock_openid_server.client_secret,
        client_id=mock_openid_server.client_id,
        algorithm=mock_openid_server.algorithm,
        domain=mock_openid_server.domain,
        audience=mock_openid_server.audience,
    )
    with mock.patch("jose.jwt.get_unverified_header", return_value=dict(kid="unmatchable")):
        with pytest.raises(AuthenticationError, match="Could not find a matching jwk"):
            manager._decode_to_payload_dict(mock_openid_server.access_token)


def test_decode(mock_openid_server):
    """
    This test verifies that a the decode() method can successfully decode a token.
    """
    manager = AsymmetricManager(
        secret=mock_openid_server.client_secret,
        client_id=mock_openid_server.client_id,
        algorithm=mock_openid_server.algorithm,
        domain=mock_openid_server.domain,
        audience=mock_openid_server.audience,
    )
    token_payload = manager.decode(mock_openid_server.access_token)
    assert token_payload.sub == "m1d1F6CmTThowu74diMLAIuNDGok5mLW@clients"
