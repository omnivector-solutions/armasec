"""
These tests verify the functionality of the RS256Decoder.
"""
import pytest

from armasec.exceptions import AuthenticationError
from armasec.schemas.jwks import JWK, JWKs
from armasec.token_decoders.rs256 import RS256Decoder


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

    decoder = RS256Decoder(jwks)
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
    decoder = RS256Decoder(jwks)
    token = build_rs256_token()
    with pytest.raises(AuthenticationError, match="Could not find a matching jwk"):
        decoder.get_decode_key(token)


def test_decode(rs256_jwk, build_rs256_token):
    """
    Verify that an RS256Decoder can successfully decode a valid jwt.
    """
    decoder = RS256Decoder(JWKs(keys=[rs256_jwk]))
    token = build_rs256_token(
        claim_overrides=dict(
            sub="test_decode-test-sub",
        ),
    )
    token_payload = decoder.decode(token)
    assert token_payload.sub == "test_decode-test-sub"
