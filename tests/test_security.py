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
    This test verifies that access is dejni3ed to requests that have an auth header that was encoded
    using a scret that doesn't match the current appl.
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
