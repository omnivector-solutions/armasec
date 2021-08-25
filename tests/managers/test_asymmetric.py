from datetime import datetime
from unittest import mock

import httpx
import jose
import pytest
import respx
import starlette

from armasec.managers import AsymmetricManager
from armasec.exceptions import AuthenticationError
from armasec.token_payload import TokenPayload


def test_load_jwks__success():
    """
    This test verifies that JWKs can be retrieved from an OIDC's well-known endpoint. Also verifies
    that the paylaods can be deserialized into JWK objects.
    """
    with respx.mock:
        jwks_route = respx.get("https://some-domain.com/.well-known/jwks.json")
        jwks_route.return_value=httpx.Response(
            starlette.status.HTTP_200_OK,
            json=dict(
                keys=[
                    dict(
                        alg='RS256',
                        e='phony',
                        kid='mocked-kid',
                        kty='RSA',
                        n='phony',
                        use='sig',
                        x5c=['phony'],
                        x5t='phony',
                    ),
                    dict(
                        alg='RS256',
                        e='dummy',
                        kid='other-kid',
                        kty='RSA',
                        n='dummy',
                        use='sig',
                        x5c=['dummy'],
                        x5t='dummy',
                    ),
                ],
            ),
        )
        manager = AsymmetricManager(
            secret="notsosecret",
            client_id="dummy-client",
            algorithm="RS256",
            domain="some-domain.com",
            audience="https://some-audience.com",
        )
        assert jwks_route.called
        assert [jwk.kid for jwk in manager.jwks] == ['mocked-kid', 'other-kid']


def test_load_jwks__fails_if_request_for_jwks_fails():
    """
    This test verifies that a call to an OIDC's well-known endpoint causes an exception to be
    raised indicating that the call failed.
    """
    with respx.mock:
        jwks_route = respx.get("https://some-domain.com/.well-known/jwks.json")
        with pytest.raises(AuthenticationError, match="Call to .* failed"):
            jwks_route.side_effect=Exception("Boom")
            manager = AsymmetricManager(
                secret="notsosecret",
                client_id="dummy-client",
                algorithm="RS256",
                domain="some-domain.com",
                audience="https://some-audience.com",
            )


def test_load_jwks__fails_if_request_status_is_not_OK():
    """
    This test verifies that a call to an OIDC's well-known endpoint causes returns an OK status code
    and that an exception is raised for other status codes.
    """
    with respx.mock:
        jwks_route = respx.get("https://some-domain.com/.well-known/jwks.json")
        with pytest.raises(AuthenticationError, match="Didn't get a success status code"):
            jwks_route.return_value=httpx.Response(starlette.status.HTTP_400_BAD_REQUEST)
            manager = AsymmetricManager(
                secret="notsosecret",
                client_id="dummy-client",
                algorithm="RS256",
                domain="some-domain.com",
                audience="https://some-audience.com",
            )


def test_load_jwks__fails_if_response_is_malformed():
    """
    This test verifies that a the data returned by an OIDC's well-known endpoint is formed as
    expected with a "key" element, and that if the data is malformed, a exception is raised.
    """
    with respx.mock:
        jwks_route = respx.get("https://some-domain.com/.well-known/jwks.json")
        with pytest.raises(AuthenticationError, match="Response jwks data is malformed"):
            jwks_route.return_value=httpx.Response(
                starlette.status.HTTP_200_OK,
                json=dict(garbage="data"),
            )
            manager = AsymmetricManager(
                secret="notsosecret",
                client_id="dummy-client",
                algorithm="RS256",
                domain="some-domain.com",
                audience="https://some-audience.com",
            )


def test__decode_to_payload_dict__success():
    """
    This test verifies that a the data _decode_to_payload_dict() method can successfully extract a
    token payload when it finds a matching public key in the JWKs.
    """
    with respx.mock:
        jwks_route = respx.get("https://some-domain.com/.well-known/jwks.json")
        jwks_route.return_value=httpx.Response(
            starlette.status.HTTP_200_OK,
            json=dict(
                keys=[
                    dict(
                        alg='RS256',
                        e='phony',
                        kid='mocked-kid',
                        kty='RSA',
                        n='phony',
                        use='sig',
                        x5c=['phony'],
                        x5t='phony',
                    )
                ],
            ),
        )
        manager = AsymmetricManager(
            secret="notsosecret",
            client_id="dummy-client",
            algorithm="RS256",
            domain="some-domain.com",
            audience="https://some-audience.com",
        )
        with mock.patch("jose.jwt.get_unverified_header", return_value=dict(kid="mocked-kid")):
            with mock.patch("jose.jwt.decode", return_value=dict(good="to go")):
                payload = manager._decode_to_payload_dict("xxx")
                assert payload == dict(good="to go")


def test__decode_to_payload_dict__fails_if_kid_not_in_unverified_header():
    """
    This test verifies that an exception is raised if the token's unverified header does not contain
    a "kid" claim.
    """
    with respx.mock:
        jwks_route = respx.get("https://some-domain.com/.well-known/jwks.json")
        jwks_route.return_value=httpx.Response(
            starlette.status.HTTP_200_OK,
            json=dict(
                keys=[
                    dict(
                        alg='RS256',
                        e='phony',
                        kid='mocked-kid',
                        kty='RSA',
                        n='phony',
                        use='sig',
                        x5c=['phony'],
                        x5t='phony',
                    )
                ],
            ),
        )
        manager = AsymmetricManager(
            secret="notsosecret",
            client_id="dummy-client",
            algorithm="RS256",
            domain="some-domain.com",
            audience="https://some-audience.com",
        )
        with mock.patch("jose.jwt.get_unverified_header", return_value=dict()):
            with pytest.raises(AuthenticationError, match="doesn't contain 'kid'"):
                payload = manager._decode_to_payload_dict("xxx")


def test__decode_to_payload_dict__fails_if_no_jwk_matches_unverified_header():
    """
    This test verifies that an exception is raised if none of the loaded JWKs match the token's
    unverified header.
    """
    with respx.mock:
        jwks_route = respx.get("https://some-domain.com/.well-known/jwks.json")
        jwks_route.return_value=httpx.Response(
            starlette.status.HTTP_200_OK,
            json=dict(
                keys=[
                    dict(
                        alg='RS256',
                        e='phony',
                        kid='mocked-kid',
                        kty='RSA',
                        n='phony',
                        use='sig',
                        x5c=['phony'],
                        x5t='phony',
                    )
                ],
            ),
        )
        manager = AsymmetricManager(
            secret="notsosecret",
            client_id="dummy-client",
            algorithm="RS256",
            domain="some-domain.com",
            audience="https://some-audience.com",
        )
        with mock.patch("jose.jwt.get_unverified_header", return_value=dict(kid="unmatchable")):
            with pytest.raises(AuthenticationError, match="Could not find a matching jwk"):
                payload = manager._decode_to_payload_dict("xxx")
