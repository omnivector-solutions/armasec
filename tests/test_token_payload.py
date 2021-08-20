from datetime import datetime

import pytest

from armasec.token_payload import TokenPayload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_to_dict():
    """
    This test veifires that the ``to_dict()`` method produces a dictionary representation of the
    TokenPayload instance's data.
    """
    payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    assert payload.to_dict() == dict(
        sub="someone",
        permissions=["a", "b", "c"],
        exp=int(datetime.utcnow().timestamp()),
    )


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_from_dict():
    """
    This test verifies that a TokenPayload instance can be correctly initialized with the data
    embedded in a properly constructed and valid jwt.
    """
    payload = TokenPayload.from_dict(
        dict(
            sub="someone",
            permissions=["a", "b", "c"],
            exp=datetime.utcnow().timestamp(),
        ),
    )
    assert payload.sub == "someone"
    assert payload.permissions == ["a", "b", "c"]
    assert payload.expire == datetime.utcnow()
