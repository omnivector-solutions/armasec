"""
These tests verify the functionality of the TokenDecoder.
"""

from unittest import mock

import pytest

from armasec.exceptions import AuthenticationError, PayloadMappingError
from armasec.schemas.jwks import JWK, JWKs
from armasec.token_decoder import TokenDecoder, extract_keycloak_permissions


def test_get_decode_key(rs256_jwk, build_rs256_token, rs256_kid):
    """
    Verify that the correct JWK is returned and matches on the 'kid' header.
    """
    jwks = JWKs(
        keys=[
            rs256_jwk,
            JWK(
                alg="RS256",
                kty="RSA",
                kid="unmatchable",
                n="threeve",
                e="AQAB",
            ),
        ],
    )

    decoder = TokenDecoder(jwks)
    token = build_rs256_token()
    key = decoder.get_decode_key(token)
    assert key["kid"] == rs256_jwk.kid


def test_get_decode_key__fail_if_kid_does_not_match(build_rs256_token):
    """
    Verify that an AuthenticationError is raised if no matching JWK is found.
    """
    jwks = JWKs(
        keys=[
            JWK(
                alg="RS256",
                kty="RSA",
                kid="unmatchable",
                n="threeve",
                e="AQAB",
            ),
        ],
    )
    decoder = TokenDecoder(jwks)
    token = build_rs256_token()
    with pytest.raises(AuthenticationError, match="Could not find a matching jwk"):
        decoder.get_decode_key(token)


def test_decode__success(rs256_jwk, build_rs256_token):
    """
    Verify that an RS256Decoder can successfully decode a valid jwt.
    """
    decoder = TokenDecoder(JWKs(keys=[rs256_jwk]))
    token = build_rs256_token(
        claim_overrides=dict(
            sub="test_decode-test-sub",
            azp="some-fake-id",
        ),
    )
    token_payload = decoder.decode(token)
    assert token_payload.sub == "test_decode-test-sub"
    assert token_payload.client_id == "some-fake-id"
    assert token_payload.original_token == token


def test_decode__fails_when_jwt_decode_throws_an_error(rs256_jwk):
    """
    This test verifies that the ``decode()`` raises an exception with a helpful message when it
    fails to decode a token.
    """
    decoder = TokenDecoder(JWKs(keys=[rs256_jwk]))
    with mock.patch("jose.jwt.decode", side_effect=Exception("BOOM!")):
        with pytest.raises(AuthenticationError, match="Failed to decode token string"):
            decoder.decode("doesn't matter what token we pass here")


def test_decode__with_permission_extractor(rs256_jwk, build_rs256_token):
    """
    Verify that an RS256Decoder can extract permissions from a valid jwt.
    """
    token = build_rs256_token(
        claim_overrides=dict(
            sub="test_decode-test-sub",
            azp="some-fake-id",
            permissions=[],
            resource_access=dict(default=dict(roles=["read:stuff", "write:stuff"])),
        ),
    )

    def extractor(token_dict):
        return token_dict["resource_access"]["default"]["roles"]

    decoder = TokenDecoder(
        JWKs(keys=[rs256_jwk]),
        permission_extractor=extractor,
    )
    token_payload = decoder.decode(token)
    assert token_payload.sub == "test_decode-test-sub"
    assert token_payload.client_id == "some-fake-id"
    assert token_payload.permissions == ["read:stuff", "write:stuff"]


def test_decode__permission_extractor_raises_error(rs256_jwk, build_rs256_token):
    """
    Verify that an RS256Decoder handles a failure in the permission extractor.

    If an exception is raised by the permission extractor, it should be handled
    by the decoder and PayloadMappingError should be raised instead.
    """
    token = build_rs256_token(
        claim_overrides=dict(
            sub="test_decode-test-sub",
            azp="some-fake-id",
            permissions=[],
            resource_access=dict(default=dict(roles=["read:stuff", "write:stuff"])),
        ),
    )

    def extractor(_):
        raise RuntimeError("Boom!")

    decoder = TokenDecoder(
        JWKs(keys=[rs256_jwk]),
        permission_extractor=extractor,
    )
    with pytest.raises(
        PayloadMappingError,
        match="Failed to map decoded token.*Boom!",
    ):
        decoder.decode(token)


def test_extract_keycloak_permissions():
    """
    Verify the `extract_keyclaok_permissons()` works as intended.

    It should correctly extract's the client's role as the permissions to be used in the
    TokenPayload.
    """
    decoded_token = {
        "exp": 1728627701,
        "iat": 1728626801,
        "jti": "24fdb7ef-d773-4e6b-982a-b8126dd58af7",
        "sub": "dfa64115-40b5-46ab-924c-c376e73f631d",
        "azp": "my-client",
        "resource_access": {
            "my-client": {"roles": ["read:stuff"]},
        },
    }

    assert extract_keycloak_permissions(decoded_token) == ["read:stuff"]
