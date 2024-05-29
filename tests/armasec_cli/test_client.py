import json
from typing import Dict, Optional

import httpx
import pydantic
import pytest

from armasec_cli.exceptions import Abort
from armasec_cli.client import _deserialize_request_model, make_request


DEFAULT_DOMAIN = "https://dummy-domain.com"


@pytest.fixture
def dummy_client():
    def _helper(
        base_url: str = DEFAULT_DOMAIN,
        headers: Optional[Dict] = None,
    ) -> httpx.Client:
        if headers is None:
            headers = dict()

        return httpx.Client(base_url=base_url, headers=headers)

    return _helper


class DummyResponseModel(pydantic.BaseModel):
    foo: int
    bar: str


class ErrorResponseModel(pydantic.BaseModel):
    error: str


def test__deserialize_request_model__success():
    request_kwargs = dict()
    _deserialize_request_model(
        DummyResponseModel(foo=1, bar="one"),
        request_kwargs,
        "Abort message does not matter here",
        "Whatever Subject",
    )
    assert json.loads(request_kwargs["content"]) == dict(foo=1, bar="one")
    assert request_kwargs["headers"] == {"Content-Type": "application/json"}


def test__deserialize_request_model__raises_Abort_if_request_kwargs_already_has_other_body_parts():
    with pytest.raises(Abort, match="Request was incorrectly structured"):
        _deserialize_request_model(
            DummyResponseModel(foo=1, bar="one"),
            dict(data=dict(foo=11)),
            "Abort message does not matter here",
            "Whatever Subject",
        )

    with pytest.raises(Abort, match="Request was incorrectly structured"):
        _deserialize_request_model(
            DummyResponseModel(foo=1, bar="one"),
            dict(json=dict(foo=11)),
            "Abort message does not matter here",
            "Whatever Subject",
        )

    with pytest.raises(Abort, match="Request was incorrectly structured"):
        _deserialize_request_model(
            DummyResponseModel(foo=1, bar="one"),
            dict(content=json.dumps(dict(foo=11))),
            "Abort message does not matter here",
            "Whatever Subject",
        )


def test_make_request__success(respx_mock, dummy_client):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"

    respx_mock.get(f"{DEFAULT_DOMAIN}{req_path}").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dict(
                foo=1,
                bar="one",
            ),
        ),
    )
    dummy_response_instance = make_request(
        client,
        req_path,
        "GET",
        expected_status=200,
        response_model_cls=DummyResponseModel,
    )
    assert isinstance(dummy_response_instance, DummyResponseModel)
    assert dummy_response_instance.foo == 1
    assert dummy_response_instance.bar == "one"


def test_make_request__raises_Abort_if_client_request_raises_exception(
    respx_mock,
    dummy_client,
):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"
    original_error = httpx.RequestError("BOOM!")

    respx_mock.get(f"{DEFAULT_DOMAIN}{req_path}").mock(side_effect=original_error)

    with pytest.raises(
        Abort, match="There was a big problem: Communication with the API failed"
    ) as err_info:
        make_request(
            client,
            req_path,
            "GET",
            abort_message="There was a big problem",
            abort_subject="BIG PROBLEM",
        )
    assert err_info.value.subject == "BIG PROBLEM"
    assert err_info.value.log_message == ("There was an error making the request to the API")
    assert err_info.value.original_error == original_error


def test_make_request__raises_Abort_with_ownership_message_for_403_for_non_owners(
    respx_mock,
    dummy_client,
):
    client = dummy_client()
    req_path = "/fake-path"

    respx_mock.delete(f"{DEFAULT_DOMAIN}{req_path}").mock(
        return_value=httpx.Response(
            httpx.codes.FORBIDDEN,
            json=dict(detail="This jabroni does not own this whingding"),
        ),
    )

    with pytest.raises(Abort, match="You do not own this resource") as err_info:
        make_request(
            client,
            req_path,
            "DELETE",
            expected_status=204,
            abort_message="There was a big problem",
            abort_subject="BIG PROBLEM",
        )
    assert err_info.value.subject == "BIG PROBLEM"
    assert "Resource could not be modified by non-owner" in err_info.value.log_message
    assert "This jabroni does not own this whingding" in err_info.value.log_message
    assert err_info.value.original_error is None


def test_make_request__raises_Abort_when_expected_status_is_not_None_and_response_does_not_match(
    respx_mock, dummy_client
):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"

    respx_mock.get(f"{DEFAULT_DOMAIN}{req_path}").mock(
        return_value=httpx.Response(
            httpx.codes.BAD_REQUEST,
            text="It blowed up",
        ),
    )

    with pytest.raises(
        Abort,
        match="There was a big problem: Received an error response",
    ) as err_info:
        make_request(
            client,
            req_path,
            "GET",
            expected_status=200,
            abort_message="There was a big problem",
            abort_subject="BIG PROBLEM",
        )
    assert err_info.value.subject == "BIG PROBLEM"
    assert err_info.value.log_message == ("Got an error code for request: 400: It blowed up")
    assert err_info.value.original_error is None


def test_make_request__does_not_raise_Abort_when_expected_status_is_None_and_response_has_fail_code(
    respx_mock, dummy_client
):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"

    respx_mock.get(f"{DEFAULT_DOMAIN}{req_path}").mock(
        return_value=httpx.Response(
            httpx.codes.BAD_REQUEST,
            json=dict(error="It blowed up"),
        ),
    )

    err = make_request(
        client,
        req_path,
        "GET",
        response_model_cls=ErrorResponseModel,
    )
    assert err.error == "It blowed up"


def test_make_request__returns_the_response_status_code_if_the_method_is_DELETE(
    respx_mock,
    dummy_client,
):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"

    respx_mock.delete(f"{DEFAULT_DOMAIN}{req_path}").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dict(error="It blowed up"),
        ),
    )

    assert make_request(client, req_path, "DELETE") == httpx.codes.OK


def test_make_request__returns_the_response_status_code_if_expect_response_is_False(
    respx_mock,
    dummy_client,
):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"

    respx_mock.post(f"{DEFAULT_DOMAIN}{req_path}").mock(
        return_value=httpx.Response(httpx.codes.BAD_REQUEST),
    )

    assert (
        make_request(
            client,
            req_path,
            "POST",
            expect_response=False,
        )
        == httpx.codes.BAD_REQUEST
    )


def test_make_request__raises_an_Abort_if_the_response_cannot_be_deserialized_with_JSON(
    respx_mock,
    dummy_client,
):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"

    respx_mock.get(f"{DEFAULT_DOMAIN}{req_path}").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            text="Not JSON, my dude",
        ),
    )

    with pytest.raises(
        Abort,
        match="There was a big problem: Response carried no data",
    ) as err_info:
        make_request(
            client,
            req_path,
            "GET",
            abort_message="There was a big problem",
            abort_subject="BIG PROBLEM",
        )
    assert err_info.value.subject == "BIG PROBLEM"
    assert err_info.value.log_message == "Failed unpacking json: Not JSON, my dude"
    assert isinstance(err_info.value.original_error, json.decoder.JSONDecodeError)


def test_make_request__returns_a_plain_dict_if_response_model_cls_is_None(
    respx_mock,
    dummy_client,
):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"

    respx_mock.get(f"{DEFAULT_DOMAIN}{req_path}").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dict(a=1, b=2, c=3),
        ),
    )

    assert make_request(client, req_path, "GET") == dict(a=1, b=2, c=3)


def test_make_request__raises_an_Abort_if_the_response_data_cannot_be_serialized(
    respx_mock, dummy_client
):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"

    respx_mock.get(f"{DEFAULT_DOMAIN}{req_path}").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dict(a=1, b=2, c=3),
        ),
    )

    with pytest.raises(
        Abort,
        match="There was a big problem: Unexpected data in response",
    ) as err_info:
        make_request(
            client,
            req_path,
            "GET",
            abort_message="There was a big problem",
            abort_subject="BIG PROBLEM",
            response_model_cls=DummyResponseModel,
        )
    assert err_info.value.subject == "BIG PROBLEM"
    assert err_info.value.log_message == (
        f"Unexpected format in response data: {dict(a=1, b=2, c=3)}"
    )
    assert isinstance(err_info.value.original_error, pydantic.ValidationError)


def test_make_request__uses_request_model_instance_for_request_body_if_passed(
    respx_mock,
    dummy_client,
):
    client = dummy_client(headers={"content-type": "garbage"})
    req_path = "/fake-path"

    dummy_route = respx_mock.post(f"{DEFAULT_DOMAIN}{req_path}")
    dummy_route.mock(
        return_value=httpx.Response(
            httpx.codes.CREATED,
            json=dict(
                foo=1,
                bar="one",
            ),
        ),
    )
    dummy_response_instance = make_request(
        client,
        req_path,
        "POST",
        expected_status=201,
        response_model_cls=DummyResponseModel,
        request_model=DummyResponseModel(foo=1, bar="one"),
    )
    assert isinstance(dummy_response_instance, DummyResponseModel)
    assert dummy_response_instance.foo == 1
    assert dummy_response_instance.bar == "one"

    assert dummy_route.calls.last.request.content == json.dumps(
        dict(foo=1, bar="one"),
        separators=(",", ":"),
    ).encode("utf-8")
    assert dummy_route.calls.last.request.headers["Content-Type"] == "application/json"
