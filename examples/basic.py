import os

from armasec import TokenManager, TokenSecurity, TokenPayload, RS256Decoder, OpenidConfigLoader
from fastapi import FastAPI, Depends
from loguru import logger


app = FastAPI()

domain = os.environ.get("ARMASEC_EXAMPLE_DOMAIN")
audience = os.environ.get("ARMASEC_AUDIENCE")

loader = OpenidConfigLoader(os.environ.get("ARMASEC_EXAMPLE_DOMAIN"), debug_logger=logger.debug)
decoder = RS256Decoder(loader.jwks, debug_logger=logger.debug)
manager = TokenManager(loader.config, decoder, audience=audience, debug_logger=logger.debug)
read_stuff_security = TokenSecurity(manager, scopes=["read:stuff"])

@app.get("/stuff")
async def get_items(token_payload: TokenPayload = Depends(read_stuff_security)):
    return dict(
        message="Successfully authenticated!",
        token_payload=token_payload,
    )
