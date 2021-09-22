from datetime import datetime, timezone

import pytest

from armasec.token_payload import TokenPayload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_to_dict():
    """
    This test verifies that the `to_dict()` method produces a dictionary representation of the
    TokenPayload instance's data.
    """
    exp = datetime(2021, 8, 13, 16, 38, 0, tzinfo=timezone.utc)
    payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=exp,
    )
    assert payload.to_dict() == dict(
        sub="someone",
        permissions=["a", "b", "c"],
        exp=int(exp.timestamp()),
    )


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_from_dict():
    """
    This test verifies that a TokenPayload instance can be correctly initialized with the data
    embedded in a properly constructed and valid jwt.
    """
    exp = datetime(2021, 8, 13, 16, 38, 0, tzinfo=timezone.utc)
    payload = TokenPayload.from_dict(
        dict(
            sub="someone",
            permissions=["a", "b", "c"],
            exp=int(exp.timestamp()),
        ),
    )
    assert payload.sub == "someone"
    assert payload.permissions == ["a", "b", "c"]
    assert payload.expire == exp
