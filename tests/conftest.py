import asgi_lifespan
import fastapi
import httpx
import pytest

from armasec.managers import TestTokenManager
from armasec.security import TokenSecurity


@pytest.fixture
def manager():
    """
    Provides an instance of a TestManager that helps with setting up tests.
    """
    return TestTokenManager(
        secret="itsasecrettoeverybody",
        algorithm="HS256",
        issuer="https://test-issuer.com",
        audience="https://test-audience.com",
    )


@pytest.fixture
async def client(manager):
    """
    Provides a FastAPI client against which httpx requests an be made. Includes a "/secure" endpoint
    that requires auth via the TokenSecurity injectable.
    """
    app = fastapi.FastAPI()
    security = TokenSecurity(manager)

    @app.get("/secure", dependencies=[fastapi.Depends(security)])
    async def _():
        return dict(good="to go")

    async with asgi_lifespan.LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            yield client
