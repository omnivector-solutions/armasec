from armasec import Armasec
from fastapi import FastAPI, Depends


app = FastAPI()
armasec = Armasec(
    domain="localhost:8080/realms/master",
    audience="http://keycloak.local",
    use_https=False,
    payload_claim_mapping=dict(permissions="resource_access.armasec_tutorial.roles"),
    debug_logger=print,
    debug_exceptions=True,
)

@app.get("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff"))])
async def check_access():
    return dict(message="Successfully authenticated!")
