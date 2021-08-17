from datetime import datetime

import pytest

from armasec.token_payload import TokenPayload


@pytest.mark.freeze_time("2021-08-12 16:38:00")
def test_to_dict__returns_a_dict_compatible_with_a_jwt_payload():
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
def test_from_dict__constructs_a_token_from_a_jwt_payload_dict():
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
