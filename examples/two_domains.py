import os

from armasec import Armasec
from armasec.schemas import DomainConfig
from fastapi import FastAPI, Depends


app = FastAPI()
armasec = Armasec(
    domains_config=[
        DomainConfig(
            domain=os.environ.get("ARMASEC_DOMAIN_1"),
            audience=os.environ.get("ARMASEC_AUDIENCE_1"),
        ),
        DomainConfig(
            domain=os.environ.get("ARMASEC_DOMAIN_2"),
            audience=os.environ.get("ARMASEC_AUDIENCE_2"),
        ),
    ],
    debug_exceptions=True,
)

@app.get("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff"))])
async def check_access():
    return dict(message="Successfully authenticated!")
