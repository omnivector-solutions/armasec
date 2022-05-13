import os

from armasec import Armasec
from armasec.schemas import DomainConfig
from fastapi import FastAPI, Depends


app = FastAPI()
armasec = Armasec(
    domain_configs=[
        DomainConfig(
            domain=os.environ.get("ARMASEC_DOMAIN"),
            audience=os.environ.get("ARMASEC_AUDIENCE"),
        ),
    ],
    debug_exceptions=True,
)

@app.get("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff"))])
async def check_access():
    return dict(message="Successfully authenticated!")
