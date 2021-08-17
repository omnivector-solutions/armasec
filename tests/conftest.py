import asgi_lifespan
import fastapi
import httpx
import jose
import pytest

from armasec.managers import TokenManager
from armasec.security import TokenSecurity
from armasec.token_payload import TokenPayload


@pytest.fixture
def encode_jwt(manager):
    def _helper(token_payload: TokenPayload, secret_override: str = None) -> str:
        claims = dict(
            **token_payload.to_dict(),
            iss=manager.issuer,
            aud=manager.audience,
        )
        return jose.jwt.encode(
            claims,
            manager.secret if not secret_override else secret_override,
            algorithm=manager.algorithm,
        )

    return _helper


@pytest.fixture
def pack_header(manager, encode_jwt):
    def _helper(token_payload: TokenPayload, **kwargs) -> dict:
        token = encode_jwt(token_payload, **kwargs)
        return {manager.header_key: f"{manager.auth_scheme} {token}"}

    return _helper


@pytest.fixture
def manager():
    return TokenManager(
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
