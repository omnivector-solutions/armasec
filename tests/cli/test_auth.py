import httpx
import pendulum
import plummet
import pytest
from jose import ExpiredSignatureError

from cli.auth import (
    fetch_auth_tokens,
    init_persona,
    refresh_access_token,
    validate_token_and_extract_identity,
)
from cli.cache import _get_token_paths
from cli.schemas import TokenSet, CliContext
from cli.exceptions import Abort
from cli.time_loop import Tick
from cli.config import init_settings
from cli.client import build_client


def test_validate_token_and_extract_identity__success(make_token):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 22:30:00",
    )
    with plummet.frozen_time("2022-02-16 21:30:00"):
        identity_data = validate_token_and_extract_identity(
            TokenSet(access_token=access_token)
        )
    assert identity_data.client_id == "dummy-client"
    assert identity_data.email == "good@email.com"


def test_validate_token_and_extract_identity__re_raises_ExpiredSignatureError(make_token):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 20:30:00",
    )
    with plummet.frozen_time("2022-02-16 21:30:00"):
        with pytest.raises(ExpiredSignatureError):
            validate_token_and_extract_identity(TokenSet(access_token=access_token))


def test_validate_token_and_extract_identity__raises_abort_on_empty_token():
    test_token_set = TokenSet(access_token="")
    with pytest.raises(Abort, match="Access token file exists but it is empty"):
        validate_token_and_extract_identity(test_token_set)


def test_validate_token_and_extract_identity__raises_abort_on_unknown_error(mocker):
    test_token_set = TokenSet(access_token="BOGUS-TOKEN")
    mocker.patch("jose.jwt.decode", side_effect=Exception("BOOM!"))
    with pytest.raises(Abort, match="There was an unknown error while validating"):
        validate_token_and_extract_identity(test_token_set)


def test_validate_token_and_extract_identity__raises_abort_if_token_is_missing_identity_data(
    make_token
):
    access_token = make_token(expires="2022-02-16 22:30:00")
    with plummet.frozen_time("2022-02-16 21:30:00"):
        with pytest.raises(Abort, match="error extracting the user's identity"):
            validate_token_and_extract_identity(TokenSet(access_token=access_token))


@pytest.mark.usefixtures("override_cache_dir")
def test_init_persona__success(make_token, mock_context):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 22:30:00",
    )
    refresh_token = "dummy-refresh-token"
    (access_token_path, refresh_token_path) = _get_token_paths()
    access_token_path.write_text(access_token)
    refresh_token_path.write_text(refresh_token)

    with plummet.frozen_time("2022-02-16 21:30:00"):
        persona = init_persona(mock_context)

    assert persona.token_set.access_token == access_token
    assert persona.token_set.refresh_token == refresh_token
    assert persona.identity_data.client_id == "dummy-client"
    assert persona.identity_data.email == "good@email.com"


@pytest.mark.usefixtures("override_cache_dir")
def test_init_persona__uses_passed_token_set(make_token, mock_context):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 22:30:00",
    )
    refresh_token = "dummy-refresh-token"
    (access_token_path, refresh_token_path) = _get_token_paths()

    token_set = TokenSet(
        access_token=access_token,
        refresh_token=refresh_token,
    )

    assert not access_token_path.exists()
    assert not refresh_token_path.exists()

    with plummet.frozen_time("2022-02-16 21:30:00"):
        persona = init_persona(mock_context, token_set)

    assert persona.token_set.access_token == access_token
    assert persona.token_set.refresh_token == refresh_token
    assert persona.identity_data.client_id == "dummy-client"
    assert persona.identity_data.email == "good@email.com"

    assert access_token_path.exists()
    assert access_token_path.read_text() == access_token
    assert refresh_token_path.exists()


@pytest.mark.usefixtures("override_cache_dir")
def test_init_persona__refreshes_access_token_if_it_is_expired(make_token, respx_mock):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 22:30:00",
    )
    refresh_token = "dummy-refresh-token"
    (access_token_path, refresh_token_path) = _get_token_paths()
    access_token_path.write_text(access_token)
    refresh_token_path.write_text(refresh_token)

    refreshed_access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-17 22:30:00",
    )

    respx_mock.post("https://test.domain/protocol/openid-connect/token").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dict(access_token=refreshed_access_token),
        ),
    )


    settings = init_settings(
        oidc_domain="test.domain",
        oidc_audience="https://test.domain/api",
        oidc_client_id="test-client-id"
    )
    client = build_client(settings)
    cli_context = CliContext(
        settings=settings,
        client=client,
    )

    with plummet.frozen_time("2022-02-16 23:30:00"):
        persona = init_persona(cli_context)

    assert persona.token_set.access_token == refreshed_access_token
    assert persona.token_set.refresh_token == refresh_token
    assert persona.identity_data.client_id == "dummy-client"
    assert persona.identity_data.email == "good@email.com"

    assert access_token_path.exists()
    assert access_token_path.read_text() == refreshed_access_token
    assert refresh_token_path.exists()
    assert refresh_token_path.read_text() == refresh_token


def test_refresh_access_token__success(make_token, respx_mock, mock_context):
    access_token = "expired-access-token"
    refresh_token = "dummy-refresh-token"
    token_set = TokenSet(access_token=access_token, refresh_token=refresh_token)

    refreshed_access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-17 22:30:00",
    )

    respx_mock.post("https://test.domain/protocol/openid-connect/token").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dict(access_token=refreshed_access_token),
        ),
    )

    settings = init_settings(
        oidc_domain="test.domain",
        oidc_audience="https://test.domain/api",
        oidc_client_id="test-client-id"
    )
    client = build_client(settings)
    cli_context = CliContext(
        settings=settings,
        client=client,
    )

    refresh_access_token(cli_context, token_set)

    assert token_set.access_token == refreshed_access_token


def test_refresh_access_token__raises_abort_on_non_200_response(respx_mock):
    access_token = "expired-access-token"
    refresh_token = "dummy-refresh-token"
    token_set = TokenSet(access_token=access_token, refresh_token=refresh_token)

    respx_mock.post("https://test.domain/protocol/openid-connect/token").mock(
        return_value=httpx.Response(
            httpx.codes.BAD_REQUEST,
            json=dict(error_description="BOOM!"),
        ),
    )

    settings = init_settings(
        oidc_domain="test.domain",
        oidc_audience="https://test.domain/api",
        oidc_client_id="test-client-id"
    )
    client = build_client(settings)
    cli_context = CliContext(
        settings=settings,
        client=client,
    )

    with pytest.raises(Abort, match="auth token could not be refreshed"):
        refresh_access_token(cli_context, token_set)


def test_fetch_auth_tokens__success(respx_mock):
    access_token = "dummy-access-token"
    refresh_token = "dummy-refresh-token"
    respx_mock.post("https://test.domain/protocol/openid-connect/auth/device").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dict(
                device_code="dummy-code",
                verification_uri_complete="https://dummy-uri.com",
                interval=1,
            ),
        ),
    )
    respx_mock.post("https://test.domain/protocol/openid-connect/token").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dict(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
        ),
    )

    settings = init_settings(
        oidc_domain="test.domain",
        oidc_audience="https://test.domain/api",
        oidc_client_id="test-client-id"
    )
    client = build_client(settings)
    cli_context = CliContext(
        settings=settings,
        client=client,
    )

    token_set = fetch_auth_tokens(cli_context)
    assert token_set.access_token == access_token
    assert token_set.refresh_token == refresh_token


def test_fetch_auth_tokens__raises_Abort_when_it_times_out_waiting_for_the_user(
    respx_mock,
    mocker,
):
    respx_mock.post("https://test.domain/protocol/openid-connect/auth/device").mock(
        return_value=httpx.Response(
            httpx.codes.OK,
            json=dict(
                device_code="dummy-code",
                verification_uri_complete="https://dummy-uri.com",
                interval=0,
            ),
        ),
    )
    respx_mock.post("https://test.domain/protocol/openid-connect/token").mock(
        return_value=httpx.Response(
            httpx.codes.BAD_REQUEST,
            json=dict(error="authorization_pending"),
        ),
    )

    settings = init_settings(
        oidc_domain="test.domain",
        oidc_audience="https://test.domain/api",
        oidc_client_id="test-client-id"
    )
    client = build_client(settings)
    cli_context = CliContext(
        settings=settings,
        client=client,
    )

    one_tick = Tick(
        counter=1,
        elapsed=pendulum.Duration(seconds=1),
        total_elapsed=pendulum.Duration(seconds=1),
    )
    mocker.patch("cli.auth.TimeLoop", return_value=[one_tick])
    with pytest.raises(Abort, match="not completed in time"):
        fetch_auth_tokens(cli_context)
