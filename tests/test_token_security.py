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

from armasec.schemas.jwks import JWKs
from armasec.token_decoders.rs256 import RS256Decoder
from armasec.token_manager import TokenManager
from armasec.token_security import TokenSecurity


@pytest.fixture
def manager(rs256_openid_config, rs256_jwk):
    """
    This fixture provides a TokenManager configured with armasec's pytest_extension jwks and
    a token decoder using the same.
    """
    jwks = JWKs(keys=[rs256_jwk])
    decoder = RS256Decoder(jwks)
    return TokenManager(rs256_openid_config, decoder)


@pytest.fixture
async def app():
    """
    Provides an instance of a FastAPI app that is to be used only for testing purposes.
    """
    return fastapi.FastAPI()


@pytest.fixture
async def build_secure_endpoint(app, manager):
    """
    Provides a method that dynamically builds a GET route on the app that requires a header with a
    valid token that includes the supplied scopes.
    """

    def _helper(path: str, scopes: Optional[List[str]] = None):
        """
        Adds a route onto the app at the provide path. If scopes are provided, they are supplied
        to the injected TokenSecurity that is added to the route.
        """

        @app.get(path, dependencies=[fastapi.Depends(TokenSecurity(manager, scopes=scopes))])
        async def _():
            return dict(good="to go")

    return _helper


@pytest.fixture
async def client(app, manager, build_secure_endpoint):
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
async def test_injector_allows_authorized_request(client, manager, build_rs256_token):
    """
    This test verifies that access is granted to requests with valid auth headers on endpoints that
    are secured by armada-security's injectable security instances.
    """
    exp = datetime(2021, 9, 17, 20, 56, 0, tzinfo=timezone.utc)
    token = build_rs256_token(
        claim_overrides=dict(sub="me", permissions=["read:all"], exp=exp.timestamp()),
    )
    headers = {"Authorization": f"bearer {token}"}
    response = await client.get("/secure", headers=headers)
    assert response.status_code == starlette.status.HTTP_200_OK


@pytest.mark.asyncio
async def test_injector_requires_correctly_encoded_token(client, manager):
    """
    This test verifies that access is denied to requests when the jwt is invalid.
    """
    headers = {"Authorization": "bearer bad-token"}
    response = await client.get("/secure", headers=headers)
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.text


@pytest.mark.asyncio
@pytest.mark.freeze_time("2021-09-16 20:56:00")
async def test_injector_requires_scopes(client, manager, build_secure_endpoint, build_rs256_token):
    """
    This test verifies that access is granted to requests with valid auth headers where the token
    carries all of the scopes required by the endpoint.
    """
    exp = datetime(2021, 9, 17, 20, 56, 0, tzinfo=timezone.utc)
    token = build_rs256_token(
        claim_overrides=dict(sub="me", permissions=["read:all"], exp=exp.timestamp()),
    )
    headers = {"Authorization": f"bearer {token}"}

    build_secure_endpoint("/requires_read_all", scopes=["read:all"])
    response = await client.get("/requires_read_all", headers=headers)
    assert response.status_code == starlette.status.HTTP_200_OK

    build_secure_endpoint("/requires_read_more", scopes=["read:all", "read:more"])
    response = await client.get("/requires_read_more", headers=headers)
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN
    assert "Not authorized" in response.text
