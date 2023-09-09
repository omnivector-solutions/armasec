"""
These tests verify the functionality of the TokenDecoder.
"""
from unittest import mock

import pytest

from armasec.exceptions import AuthenticationError, PayloadMappingError
from armasec.schemas.jwks import JWK, JWKs
from armasec.token_decoder import TokenDecoder


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


def test_decode__fails_when_jwt_decode_throws_an_error(rs256_jwk):
    """
    This test verifies that the ``decode()`` raises an exception with a helpful message when it
    fails to decode a token.
    """
    decoder = TokenDecoder(JWKs(keys=[rs256_jwk]))
    with mock.patch("jose.jwt.decode", side_effect=Exception("BOOM!")):
        with pytest.raises(AuthenticationError, match="Failed to decode token string"):
            decoder.decode("doesn't matter what token we pass here")


def test_decode__with_payload_claim_mapping(rs256_jwk, build_rs256_token):
    """
    Verify that an RS256Decoder applies a payload_claim_mapping to a valid jwt.
    """
    token = build_rs256_token(
        claim_overrides=dict(
            sub="test_decode-test-sub",
            azp="some-fake-id",
            permissions=[],
            resource_access=dict(default=dict(roles=["read:stuff", "write:stuff"])),
        ),
    )
    decoder = TokenDecoder(
        JWKs(keys=[rs256_jwk]),
        payload_claim_mapping=dict(permissions="resource_access.default.roles"),
    )
    token_payload = decoder.decode(token)
    assert token_payload.sub == "test_decode-test-sub"
    assert token_payload.client_id == "some-fake-id"
    assert token_payload.permissions == ["read:stuff", "write:stuff"]


def test_decode__missing_payload_claim_mapping(rs256_jwk, build_rs256_token):
    """
    Verify that an RS256Decoder throws an error if mapping failed.

    There will be an error if there is a missing claim mapping.
    There will be an error if the jmespath expression is invalid.
    """
    token = build_rs256_token(
        claim_overrides=dict(
            sub="test_decode-test-sub",
            azp="some-fake-id",
        ),
    )
    decoder = TokenDecoder(
        JWKs(keys=[rs256_jwk]),
        payload_claim_mapping=dict(foo="bar.baz"),
    )
    with pytest.raises(PayloadMappingError, match="Failed to map decoded token.*No matching values"):
        decoder.decode(token)

    decoder = TokenDecoder(
        JWKs(keys=[rs256_jwk]),
        payload_claim_mapping=dict(foo="bar-baz"),
    )
    with pytest.raises(PayloadMappingError, match="Failed to map decoded token.*Bad jmespath expression"):
        decoder.decode(token)
