import typing

import asgi_lifespan
import fastapi
import httpx
import pytest

from armasec.managers import TokenManager
from armasec.security import TokenSecurity

pytest.plugins = ["armasec.mock_oidc"]


@pytest.fixture
def manager():
    """
    Provides an instance of a TestManager that helps with setting up tests.
    """
    return TokenManager(
        secret="itsasecrettoeverybody",
        algorithm="HS256",
        issuer="https://test-issuer.com",
        audience="https://test-audience.com",
    )


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

    def _helper(path: str, scopes: typing.Optional[typing.List[str]] = None):
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
