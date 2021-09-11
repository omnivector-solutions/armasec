import json
from datetime import datetime, timezone
from unittest import mock

import pytest

from armasec.exceptions import AuthenticationError
from armasec.token_decoders.base import TokenDecoder
from armasec.token_payload import TokenPayload


@pytest.fixture()
def json_decoder():
    """
    This fixture provides an instance of a JsonDecoder class that can be used for simple tests.
    """

    class JsonDecoder(TokenDecoder):
        algorithm = "fake"

        def get_decode_key(self, token: str):
            return None

    def json_decode(token: str, *args, **kwargs) -> dict:
        return json.loads(token)

    with mock.patch("jose.jwt.decode", side_effect=json_decode):
        yield JsonDecoder()


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_decode__success(json_decoder):
    """
    This test verifies that the ``decode()`` method can successfully unpack a token into a
    TokenPayload containing the payload elements.
    """
    exp = datetime(2021, 8, 13, 16, 38, 0, tzinfo=timezone.utc)
    original_payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=exp,
    )
    token = json.dumps(original_payload.to_dict())
    extracted_payload = json_decoder.decode(token)
    assert extracted_payload == original_payload


def test_decode__fails_when_jwt_decode_throws_an_error(json_decoder):
    """
    This test verifies that the ``decode()`` raises an exception with a helpful message when it
    fails to decode a token.
    """
    with mock.patch("jose.jwt.decode", side_effect=Exception("BOOM!")):
        with pytest.raises(AuthenticationError, match="Failed to decode token string"):
            json_decoder.decode("doesn't matter what token we pass here")
