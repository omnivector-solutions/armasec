import asgi_lifespan
import fastapi
import httpx
import pytest

from armasec.managers import TestTokenManager
from armasec.security import TokenSecurity


@pytest.fixture
def manager():
    """
    Produes an instance of a Test Manager with convenience for setting up tests
    """
    return TestTokenManager(
        secret="itsasecrettoeverybody",
        algorithm="HS256",
        issuer="https://test-issuer.com",
        audience="https://test-audience.com",
    )


@pytest.fixture
def security(manager):
    return TokenSecurity(manager)


@pytest.fixture
async def client(security):
    app = fastapi.FastAPI()

    @app.get("/secure", dependencies=[fastapi.Depends(security)])
    async def _():
        return dict(good="to go")

    async with asgi_lifespan.LifespanManager(app):
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            yield client
