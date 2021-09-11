"""
These tests verify the functionality of the HS256Decoder.
"""
from datetime import datetime, timezone

import jose
import pytest

from armasec.token_decoders.hs256 import HS256Decoder


def test_get_decode_key():
    """
    Verify that the decoder's secret is returned.
    """
    decoder = HS256Decoder("my secret")
    assert decoder.get_decode_key("doesn't matter") == "my secret"


@pytest.mark.freeze_time("2021-09-16 20:56:00")
def test_decode():
    """
    Verify that the decoder can decode and verify a jwt signed with the HS256 algorithm
    """
    exp = datetime(2021, 9, 17, 20, 56, 0, tzinfo=timezone.utc)
    token = jose.jwt.encode(
        dict(sub="me", permissions=["read:all"], exp=exp.timestamp()),
        "my secret",
        algorithm="HS256",
    )
    decoder = HS256Decoder("my secret")
    token_payload = decoder.decode(token)
    assert token_payload.sub == "me"
    assert token_payload.expire == exp
    assert token_payload.permissions == ["read:all"]
