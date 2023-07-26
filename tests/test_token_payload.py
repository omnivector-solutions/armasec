import pendulum
from plummet import frozen_time

from armasec.token_payload import TokenPayload


@frozen_time("2021-08-12 16:38:00")
def test_to_dict():
    """
    This test verifies that the `to_dict()` method produces a dictionary representation of the
    TokenPayload instance's data.
    """
    exp = pendulum.parse("2021-08-13 16:38:00", tz="UTC")
    payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=exp,
        client_id="some-fake-id",
    )
    assert payload.to_dict() == dict(
        sub="someone",
        permissions=["a", "b", "c"],
        exp=int(exp.timestamp()),
        client_id="some-fake-id",
    )


@frozen_time("2021-08-12 16:38:00")
def test_from_dict():
    """
    This test verifies that a TokenPayload instance can be correctly initialized with the data
    embedded in a properly constructed and valid jwt.
    """
    exp = pendulum.parse("2021-08-13 16:38:00", tz="UTC")
    payload = TokenPayload(
        **dict(
            sub="someone",
            permissions=["a", "b", "c"],
            exp=int(exp.timestamp()),
            azp="some-fake-id",
        ),
    )
    assert payload.sub == "someone"
    assert payload.permissions == ["a", "b", "c"]
    assert payload.expire == exp
    assert payload.client_id == "some-fake-id"
