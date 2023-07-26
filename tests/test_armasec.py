"""
Test the Armasec convenience class.
"""
import asgi_lifespan
import fastapi
import httpx
import pendulum
import pytest
import starlette
from fastapi import HTTPException
from plummet import frozen_time

from armasec import Armasec, TokenSecurity


@pytest.fixture
async def app():
    """
    Provides an instance of a FastAPI app that is to be used only for testing purposes.
    """
    return fastapi.FastAPI()


@pytest.fixture
async def build_secure_endpoint(app):
    """
    Provides a method that dynamically builds a GET route on the app that requires a header with a
    valid token that includes the supplied scopes.
    """

    def _helper(path: str, security: TokenSecurity):
        """
        Adds a route onto the app at the provide path that is secured by the provided Armasec
        instance.
        """

        @app.get(path, dependencies=[fastapi.Depends(security)])
        async def _():
            return dict(good="to go")

    return _helper


@pytest.fixture
async def client(app):
    """
    Provides a FastAPI client against which httpx requests can be made. Includes a "/secure"
    endpoint that requires auth via the TokenSecurity injectable.
    """
    async with asgi_lifespan.LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url="http://armasec-test") as client:
            yield client


@frozen_time("2021-09-20 11:02:00")
async def test_lockdown__with_no_scopes(
    mock_openid_server,
    rs256_domain,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test that lockdown works correctly when supplied no scopes.
    """

    armasec = Armasec(domain=rs256_domain, audience="https://this.api")

    exp = pendulum.parse("2021-09-21 11:02:00", tz="UTC")
    token = build_rs256_token(claim_overrides=dict(sub="me", exp=exp.timestamp()))
    build_secure_endpoint("/secured-no-scopes", armasec.lockdown())

    response = await client.get("/secured-no-scopes", headers={"Authorization": f"bearer {token}"})
    assert response.status_code == starlette.status.HTTP_200_OK

    response = await client.get("/secured-no-scopes")
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED


@frozen_time("2021-09-20 11:02:00")
async def test_lockdown__with_scopes(
    mock_openid_server,
    rs256_domain,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test that lockdown works correctly when supplied with scopes.
    """

    armasec = Armasec(domain=rs256_domain, audience="https://this.api")
    build_secure_endpoint("/secured-with-scopes", armasec.lockdown("read:more"))

    good_token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=pendulum.parse("2021-09-21 11:02:00", tz="UTC").timestamp(),
            permissions=["read:more"],
        ),
    )
    response = await client.get(
        "/secured-with-scopes",
        headers={"Authorization": f"bearer {good_token}"},
    )
    assert response.status_code == starlette.status.HTTP_200_OK

    bad_token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=pendulum.parse("2021-09-21 11:02:00", tz="UTC").timestamp(),
        ),
    )
    response = await client.get(
        "/secured-with-scopes",
        headers={"Authorization": f"bearer {bad_token}"},
    )
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN


@frozen_time("2021-09-22 22:54:00")
async def test_lockdown__with_all_scopes(
    mock_openid_server,
    rs256_domain,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test that lockdown works correctly requiring all scopes.
    """

    armasec = Armasec(domain=rs256_domain, audience="https://this.api")
    build_secure_endpoint("/secured-with-scopes", armasec.lockdown_all("read:one", "read:more"))

    good_token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=pendulum.parse("2021-09-23 22:54:00", tz="UTC").timestamp(),
            permissions=["read:one", "read:more"],
        ),
    )
    response = await client.get(
        "/secured-with-scopes",
        headers={"Authorization": f"bearer {good_token}"},
    )
    assert response.status_code == starlette.status.HTTP_200_OK

    bad_token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=pendulum.parse("2021-09-23 22:54:00", tz="UTC").timestamp(),
            permissions=["read:one"],
        ),
    )
    response = await client.get(
        "/secured-with-scopes",
        headers={"Authorization": f"bearer {bad_token}"},
    )
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN


@frozen_time("2021-09-22 22:54:00")
async def test_lockdown__with_some_scopes(
    mock_openid_server,
    rs256_domain,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test that lockdown works correctly requiring some scopes.
    """

    armasec = Armasec(domain=rs256_domain, audience="https://this.api")
    build_secure_endpoint("/secured-with-scopes", armasec.lockdown_some("read:one", "read:more"))

    good_token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=pendulum.parse("2021-09-23 22:54:00", tz="UTC").timestamp(),
            permissions=["read:one"],
        ),
    )
    response = await client.get(
        "/secured-with-scopes",
        headers={"Authorization": f"bearer {good_token}"},
    )
    assert response.status_code == starlette.status.HTTP_200_OK

    bad_token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=pendulum.parse("2021-09-23 22:54:00", tz="UTC").timestamp(),
            permissions=[],
        ),
    )
    response = await client.get(
        "/secured-with-scopes",
        headers={"Authorization": f"bearer {bad_token}"},
    )
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN


@frozen_time("2021-09-20 11:02:00")
async def test_lockdown__with_two_domains__secondary_one_is_mocked(
    mock_openid_server,
    rs256_domain_config,
    rs256_secondary_domain_config,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test that lockdown works correctly when supplied two domains to the Armasec class. The secondary
    input domain is the one to match the tokens and authenticate the incoming token.
    """

    armasec = Armasec(domain_configs=[rs256_secondary_domain_config, rs256_domain_config])

    exp = pendulum.parse("2021-09-21 11:02:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(sub="me", exp=exp.timestamp(), permissions=["read:stuff"])
    )
    build_secure_endpoint("/secured-no-scopes", armasec.lockdown("read:stuff"))

    response = await client.get("/secured-no-scopes", headers={"Authorization": f"bearer {token}"})
    assert response.status_code == starlette.status.HTTP_200_OK

    response = await client.get("/secured-no-scopes")
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED


@frozen_time("2021-09-20 11:02:00")
async def test_lockdown__with_two_domains__first_one_is_mocked(
    mock_openid_server,
    rs256_domain_config,
    rs256_secondary_domain_config,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test that lockdown works correctly when supplied two domains to the Armasec class. The first
    input domain is the one to match the tokens and authenticate the incoming token.
    """

    armasec = Armasec(domain_configs=[rs256_domain_config, rs256_secondary_domain_config])

    exp = pendulum.parse("2021-09-21 11:02:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(sub="me", exp=exp.timestamp(), permissions=["read:stuff"])
    )
    build_secure_endpoint("/secured-no-scopes", armasec.lockdown("read:stuff"))

    response = await client.get("/secured-no-scopes", headers={"Authorization": f"bearer {token}"})
    assert response.status_code == starlette.status.HTTP_200_OK

    response = await client.get("/secured-no-scopes")
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED


@frozen_time("2021-09-20 11:02:00")
async def test_lockdown__with_two_domains__check_if_passing_domain_takes_precedence_over_the_domain_configs_list(  # noqa
    mock_openid_server,
    rs256_domain,
    rs256_secondary_domain_config,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test if the Armasec class works properly when both domain_configs and domain are inputted. The
    expected behaviour is the domain itself to take precedence over the domain config list.
    """

    armasec = Armasec(
        domain_configs=[rs256_secondary_domain_config],
        domain=rs256_domain,
        audience="https://this.api",
    )

    exp = pendulum.parse("2021-09-21 11:02:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(sub="me", exp=exp.timestamp(), permissions=["read:stuff"])
    )
    build_secure_endpoint("/secured-no-scopes", armasec.lockdown("read:stuff"))

    response = await client.get("/secured-no-scopes", headers={"Authorization": f"bearer {token}"})
    assert response.status_code == starlette.status.HTTP_200_OK

    response = await client.get("/secured-no-scopes")
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED


@frozen_time("2021-09-20 11:02:00")
async def test_lockdown__check_if_its_possible_to_pass_only_one_domain_config_as_a_list(
    mock_openid_server,
    rs256_domain_config,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test if the Armasec class works properly only when the domain config list is provided.
    """

    armasec = Armasec(domain_configs=[rs256_domain_config])

    exp = pendulum.parse("2021-09-21 11:02:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(sub="me", exp=exp.timestamp(), permissions=["read:stuff"])
    )
    build_secure_endpoint("/secured-no-scopes", armasec.lockdown("read:stuff"))

    response = await client.get("/secured-no-scopes", headers={"Authorization": f"bearer {token}"})
    assert response.status_code == starlette.status.HTTP_200_OK

    response = await client.get("/secured-no-scopes")
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED


@frozen_time("2021-09-20 11:02:00")
def test_armasec__no_domain_was_inputted():
    """
    Test if error is raised when neither domain nor domain_configs are provided to Armasec's class.
    """

    with pytest.raises(HTTPException) as err:
        Armasec()

    assert err.value.status_code == starlette.status.HTTP_422_UNPROCESSABLE_ENTITY
    assert err.value.detail == "No domain was input."


@frozen_time("2021-09-20 11:02:00")
@pytest.mark.parametrize(
    "key_value_pairs_to_match",
    [
        {"custom-key": "custom-value"},
        {"custom-key-1": "custom-value-1", "custom-key-2": "custom-value-2"},
        {"custom-key": ["custom-value"]},
        {"custom-key": ["custom-value-1", "custom-value-2"]},
        {"custom-key": True},
        {"custom-key": 1},
        {"custom-key": 1.0},
        {"custom-key": {"another-custom-key": "custom-value"}},
    ],
)
async def test_lockdown__test_match_keys__check_if_can_authorize(
    key_value_pairs_to_match,
    mock_openid_server,
    rs256_domain_config,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test that lockdown works correctly when supplied two domains to the Armasec class. The first
    input domain is the one to match the tokens and authenticate the incoming token.
    """
    rs256_domain_config.match_keys = key_value_pairs_to_match

    armasec = Armasec(domain_configs=[rs256_domain_config])

    exp = pendulum.parse("2021-09-21 11:02:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(
            sub="me", exp=exp.timestamp(), permissions=["read:stuff"], **key_value_pairs_to_match
        )
    )
    build_secure_endpoint("/secured-no-scopes", armasec.lockdown("read:stuff"))

    response = await client.get("/secured-no-scopes", headers={"Authorization": f"bearer {token}"})
    assert response.status_code == starlette.status.HTTP_200_OK

    response = await client.get("/secured-no-scopes")
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED


@frozen_time("2021-09-20 11:02:00")
@pytest.mark.parametrize(
    "key_value_pairs_to_match",
    [
        {"custom-key": "custom-value"},
        {"custom-key-1": "custom-value-1", "custom-key-2": "custom-value-2"},
        {"custom-key": ["custom-value"]},
        {"custom-key": ["custom-value-1", "custom-value-2"]},
        {"custom-key": True},
        {"custom-key": 1},
        {"custom-key": 1.0},
        {"custom-key": {"another-custom-key": "custom-value"}},
    ],
)
async def test_lockdown__test_match_keys__check_if_cannot_authorize(
    key_value_pairs_to_match,
    mock_openid_server,
    rs256_domain_config,
    build_rs256_token,
    build_secure_endpoint,
    app,
    client,
):
    """
    Test that lockdown works correctly when supplied two domains to the Armasec class. The first
    input domain is the one to match the tokens and authenticate the incoming token.
    """
    rs256_domain_config.match_keys = key_value_pairs_to_match

    armasec = Armasec(domain_configs=[rs256_domain_config])

    exp = pendulum.parse("2021-09-21 11:02:00", tz="UTC")
    token = build_rs256_token(
        claim_overrides=dict(sub="me", exp=exp.timestamp(), permissions=["read:stuff"])
    )
    build_secure_endpoint("/secured-no-scopes", armasec.lockdown("read:stuff"))

    response = await client.get("/secured-no-scopes", headers={"Authorization": f"bearer {token}"})
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN
