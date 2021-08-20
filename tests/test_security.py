from datetime import datetime

import pytest
import starlette

from armasec.token_payload import TokenPayload


@pytest.mark.asyncio
async def test_injector_allows_authorized_request(client, manager):
    token_payload = TokenPayload(
        sub="someone",
        permissions=["a", "b", "c"],
        expire=datetime.utcnow(),
    )
    response = await client.get("/secure", headers=manager.pack_header(token_payload))
    assert response.status_code == starlette.status.HTTP_200_OK


@pytest.mark.asyncio
async def test_injector_requires_token_header(client):
    response = await client.get("/secure")
    assert response.status_code == starlette.status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.text


@pytest.mark.asyncio
async def test_injector_requires_correctly_encoded_token(client, manager):
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
