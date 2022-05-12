"""
Verify that the TokenSecurity functions as expected with FastAPI's dependeny injection on endpoints
"""
from datetime import datetime, timezone
from typing import List, Optional

import asgi_lifespan
import fastapi
import httpx
import pytest
import starlette

from armasec.token_security import PermissionMode, TokenSecurity


@pytest.fixture
async def app():
    """
    Provides an instance of a FastAPI app that is to be used only for testing purposes.
    """
    return fastapi.FastAPI()


@pytest.fixture
async def build_secure_endpoint(app, rs256_domain_config, mock_openid_server, rs256_jwk):
    """
    Provides a method that dynamically builds a GET route on the app that requires a header with a
    valid token that includes the supplied scopes.
    """

    def _helper(
        path: str,
        scopes: Optional[List[str]] = None,
        permission_mode: PermissionMode = PermissionMode.ALL,
    ):
        """
        Adds a route onto the app at the provide path. If scopes are provided, they are supplied
        to the injected TokenSecurity that is added to the route. Uses supplied permission_mode if
        supplied
        """

        @app.get(
            path,
            dependencies=[
                fastapi.Depends(
                    TokenSecurity(
                        [rs256_domain_config], scopes=scopes, permission_mode=permission_mode
                    )
                ),
            ],
        )
        async def _():
            return dict(good="to go")

    return _helper


@pytest.fixture
async def client(app, build_secure_endpoint):
    """
    Provides a FastAPI client against which httpx requests can be made. Includes a "/secure"
    endpoint that requires auth via the TokenSecurity injectable.
    """
    build_secure_endpoint("/secure")
    async with asgi_lifespan.LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            yield client


@pytest.mark.asyncio
@pytest.mark.freeze_time("2021-09-16 20:56:00")
async def test_injector_allows_authorized_request(client, build_rs256_token):
    """
    This test verifies that access is granted to requests with valid auth headers on endpoints that
    are secured by armasec's injectable security instances.
    """
    exp = datetime(2021, 9, 17, 20, 56, 0, tzinfo=timezone.utc)
    token = build_rs256_token(
        claim_overrides=dict(sub="me", permissions=["read:all"], exp=exp.timestamp()),
    )
    headers = {"Authorization": f"bearer {token}"}
    response = await client.get("/secure", headers=headers)
    assert response.status_code == starlette.status.HTTP_200_OK


@pytest.mark.asyncio
async def test_injector_requires_correctly_encoded_token(client):
    """
    This test verifies that access is denied to requests when the jwt is invalid.
    """
    headers = {"Authorization": "bearer bad-token"}
    response = await client.get("/secure", headers=headers)
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.text


@pytest.mark.asyncio
@pytest.mark.freeze_time("2021-09-16 20:56:00")
async def test_injector_requires_all_scopes(client, build_secure_endpoint, build_rs256_token):
    """
    This test verifies that access is granted to requests with valid auth headers where the token
    carries all of the scopes required by the endpoint.
    """
    exp = datetime(2021, 9, 17, 20, 56, 0, tzinfo=timezone.utc)
    token = build_rs256_token(
        claim_overrides=dict(sub="me", permissions=["read:all", "read:other"], exp=exp.timestamp()),
    )
    headers = {"Authorization": f"bearer {token}"}

    build_secure_endpoint("/requires_read_all", scopes=["read:all"])
    response = await client.get("/requires_read_all", headers=headers)
    assert response.status_code == starlette.status.HTTP_200_OK

    build_secure_endpoint("/requires_read_more", scopes=["read:all", "read:more"])
    response = await client.get("/requires_read_more", headers=headers)
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN
    assert "Not authorized" in response.text


@pytest.mark.asyncio
@pytest.mark.freeze_time("2021-09-27 22:22:00")
async def test_injector_requires_some_scopes(client, build_secure_endpoint, build_rs256_token):
    """
    This test verifies that access is granted to requests with valid auth headers where the token
    carries some of the scopes required by the endpoint.
    """
    exp = datetime(2021, 9, 28, 22, 22, 0, tzinfo=timezone.utc)
    token = build_rs256_token(
        claim_overrides=dict(sub="me", permissions=["read:all", "read:other"], exp=exp.timestamp()),
    )
    headers = {"Authorization": f"bearer {token}"}

    build_secure_endpoint(
        "/requires_read_all",
        scopes=["read:all"],
        permission_mode=PermissionMode.SOME,
    )
    response = await client.get("/requires_read_all", headers=headers)
    assert response.status_code == starlette.status.HTTP_200_OK

    token = build_rs256_token(
        claim_overrides=dict(sub="me", permissions=["read:something-else"], exp=exp.timestamp()),
    )
    headers = {"Authorization": f"bearer {token}"}
    build_secure_endpoint(
        "/requires_read_more",
        scopes=["read:all", "read:more"],
        permission_mode=PermissionMode.SOME,
    )
    response = await client.get("/requires_read_more", headers=headers)
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN
    assert "Not authorized" in response.text


@pytest.mark.asyncio
@pytest.mark.freeze_time("2021-09-27 22:22:00")
async def test_injector_raises_error_on_unknown_permission_mode(
    client, build_secure_endpoint, build_rs256_token
):
    """
    This test verifies that a request is unauthorized if an unkown permission mode is set.
    """
    exp = datetime(2021, 9, 28, 22, 22, 0, tzinfo=timezone.utc)
    token = build_rs256_token(
        claim_overrides=dict(sub="me", permissions=["read:all"], exp=exp.timestamp()),
    )
    headers = {"Authorization": f"bearer {token}"}

    build_secure_endpoint(
        "/requires_read_all",
        scopes=["read:all"],
        permission_mode="Not a real permission",  # type: ignore
    )
    response = await client.get("/requires_read_all", headers=headers)
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN
