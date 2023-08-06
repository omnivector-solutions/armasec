from fastapi import FastAPI, Depends, status
from starlette.responses import JSONResponse
from logging import basicConfig, getLogger
from os import environ

from armasec.token_security import ManagerConfig
from armasec.schemas.armasec_config import DomainConfig
from armasec import OpenidConfigLoader, TokenManager
from armasec import TokenDecoder, TokenSecurity

# logging so we can see requests to openid endpoints
basicConfig(level="INFO")
log = getLogger(__name__)

# oidc_issuer = "your.keycloak.domain/realms/yourRealm"
oidc_issuer = environ.get("OIDC_ISSUER")
# oidc_audience is set up in client configuration in keycloak,
# the token should include this value in the `aud` claim
# oidc_audience = "someAudience"
oidc_audience = environ.get("OIDC_AUDIENCE")

log.info("Initializing Armasec...")

openid_config = OpenidConfigLoader(domain=oidc_issuer, use_https=True)

domain_config = DomainConfig(domain=oidc_issuer, audience=oidc_audience)

token_decoder = TokenDecoder(jwks=openid_config.jwks)

token_manager = TokenManager(
    openid_config=openid_config, token_decoder=token_decoder, audience=oidc_audience
)

token_manager_config = ManagerConfig(manager=token_manager, domain_config=domain_config)

armasec = TokenSecurity(domain_configs=[domain_config])

armasec.managers = [token_manager_config]

log.info("Starting FastAPI...")

app = FastAPI()


@app.get("/", dependencies=[Depends(armasec)])
async def root():
    return JSONResponse(content={"status": "you are authenticated"}, status_code=status.HTTP_200_OK)
