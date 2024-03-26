import os
import sys

from armasec import Armasec, TokenPayload
from armasec.exceptions import ArmasecError
from armasec.pluggable import hookimpl, plugin_manager
from fastapi import FastAPI, Depends
from loguru import logger
from pydantic import BaseModel
from starlette import status

# Local data store for added "subscribers" for this demo
subscribers = set()

class Subscriber(BaseModel):
    email: str


# Custom plugin code
class PluginError(ArmasecError):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    detail = "User is not subscribed."


@hookimpl
def armasec_plugin_check(token_payload: TokenPayload):
    logger.debug("Applying check from example plugin")
    PluginError.require_condition(
        getattr(token_payload, "email") in subscribers,
        "User is not subscribed!",
    )

plugin_manager.register(sys.modules[__name__])


# FastAPI app definition
app = FastAPI()
armasec = Armasec(
    domain=os.environ.get("ARMASEC_DOMAIN"),
    audience=os.environ.get("ARMASEC_AUDIENCE"),
    payload_claim_mapping=dict(permissions="resource_access.armasec_tutorial.roles"),
    use_https=False,
    debug_logger=logger.debug,
)

@app.get("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff"))])
async def check_access():
    return dict(message="Successfully authenticated!")


@app.post("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff", skip_plugins=True))])
async def add_subscriber(subscriber: Subscriber):
    subscribers.add(subscriber.email)
    return dict(message=f"Added subscriber {subscriber.email}!")
