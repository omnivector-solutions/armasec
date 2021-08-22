from datetime import datetime

import pytest
import starlette

from armasec.token_payload import TokenPayload


@pytest.mark.asyncio
async def test_injector_allows_authorized_request(client, manager):
    """
    This test verifies that access is granted to requests with valid auth headers on endpoints that
    are secured by armada-security's injectable security instances.
    """
    token_payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    response = await client.get("/secure", headers=manager.pack_header(token_payload))
    assert response.status_code == starlette.status.HTTP_200_OK


@pytest.mark.asyncio
async def test_injector_requires_token_header(client):
    """
    This test verifies that access is denied to requests witout valid auth headers on endpoints that
    are secured by armada-security's injectable security instances.
    """
    response = await client.get("/secure")
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.text


@pytest.mark.asyncio
async def test_injector_requires_correctly_encoded_token(client, manager):
    """
    This test verifies that access is denied to requests when the jwt was encoded using a the wrong
    scret (i.e. different from the secret that the TokenManager was initialized with).
    """
    token_payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    response = await client.get(
        "/secure",
        headers=manager.pack_header(token_payload, secret_override="someothersecret"),
    )
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.text


@pytest.mark.asyncio
async def test_injector_requires_scopes(client, manager, build_secure_endpoint):
    """
    This test verifies that access is granted to requests with valid auth headers where the token
    carries all of the scopes required by the endpoint.
    """
    ac_payload = TokenPayload(
        sub="someone",
        permissions=["a", "c"],
        expire=datetime.utcnow(),
    )

    build_secure_endpoint("/requires_c", scopes=["c"])
    response = await client.get("/requires_c", headers=manager.pack_header(ac_payload))
    assert response.status_code == starlette.status.HTTP_200_OK

    build_secure_endpoint("/requires_a_b_c", scopes=["a", "b", "c"])
    response = await client.get("/requires_a_b_c", headers=manager.pack_header(ac_payload))
    assert response.status_code == starlette.status.HTTP_403_FORBIDDEN
    assert "Not authorized" in response.text
