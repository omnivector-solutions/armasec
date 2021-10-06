"""
Test the Armasec convenience class.
"""
from datetime import datetime, timezone

import asgi_lifespan
import fastapi
import httpx
import pytest
import starlette

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


@pytest.mark.asyncio
@pytest.mark.freeze_time("2021-09-20 11:02:00")
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

    armasec = Armasec(rs256_domain, audience="https://this.api")

    exp = datetime(2021, 9, 21, 11, 2, 0, tzinfo=timezone.utc)
    token = build_rs256_token(claim_overrides=dict(sub="me", exp=exp.timestamp()))
    build_secure_endpoint("/secured-no-scopes", armasec.lockdown())

    response = await client.get("/secured-no-scopes", headers={"Authorization": f"bearer {token}"})
    assert response.status_code == starlette.status.HTTP_200_OK

    response = await client.get("/secured-no-scopes")
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@pytest.mark.freeze_time("2021-09-20 11:02:00")
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

    armasec = Armasec(rs256_domain, audience="https://this.api")
    build_secure_endpoint("/secured-with-scopes", armasec.lockdown("read:more"))

    good_token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=datetime(2021, 9, 21, 11, 2, 0, tzinfo=timezone.utc).timestamp(),
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
            exp=datetime(2021, 9, 21, 11, 2, 0, tzinfo=timezone.utc).timestamp(),
        ),
    )
    response = await client.get(
        "/secured-with-scopes",
        headers={"Authorization": f"bearer {bad_token}"},
    )
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.freeze_time("2021-09-22 22:54:00")
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

    armasec = Armasec(rs256_domain, audience="https://this.api")
    build_secure_endpoint("/secured-with-scopes", armasec.lockdown_all("read:one", "read:more"))

    good_token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=datetime(2021, 9, 23, 22, 54, 0, tzinfo=timezone.utc).timestamp(),
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
            exp=datetime(2021, 9, 23, 22, 54, 0, tzinfo=timezone.utc).timestamp(),
            permissions=["read:one"],
        ),
    )
    response = await client.get(
        "/secured-with-scopes",
        headers={"Authorization": f"bearer {bad_token}"},
    )
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.freeze_time("2021-09-22 22:54:00")
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

    armasec = Armasec(rs256_domain, audience="https://this.api")
    build_secure_endpoint("/secured-with-scopes", armasec.lockdown_some("read:one", "read:more"))

    good_token = build_rs256_token(
        claim_overrides=dict(
            sub="me",
            exp=datetime(2021, 9, 23, 22, 54, 0, tzinfo=timezone.utc).timestamp(),
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
            exp=datetime(2021, 9, 23, 22, 54, 0, tzinfo=timezone.utc).timestamp(),
            permissions=[],
        ),
    )
    response = await client.get(
        "/secured-with-scopes",
        headers={"Authorization": f"bearer {bad_token}"},
    )
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN
