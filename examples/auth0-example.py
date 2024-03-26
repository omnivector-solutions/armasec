from fastapi import FastAPI, Depends

from armasec_fastapi import Armasec


app = FastAPI()
armasec = Armasec(
    domain="auth0-armasec-tutorial.us.auth0.com",
    audience="https://auth0-api",
    debug_logger=print,
    debug_exceptions=True,
)

@app.get("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff"))])
async def check_access():
    return dict(message="Successfully authenticated!")
