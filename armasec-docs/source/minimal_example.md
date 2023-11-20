# Minimal Example

The following is a minimal example of how to configure your API to enforce security on endpoints
using tokens issued by Auth0.

First, create a file named `example.py` with the following contents:

```python title="example.py" linenums="1"
import os

from armasec import Armasec
from fastapi import FastAPI, Depends


app = FastAPI()
armasec = Armasec(
    domain=os.environ.get("ARMASEC_DOMAIN"),
    audience=os.environ.get("ARMASEC_AUDIENCE"),
)

@app.get("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff"))])
async def check_access():
    return dict(message="Successfully authenticated!")
```

In this example, you would have set two environment variables for your project settings:

- `ARMASEC_DOMAIN`
  - This would be your Auth0 domain
  - Example: `my-auth.us.auth0.com`
- `ARMASEC_AUDIENCE`
  - You get this from your Auth0 API App
  - Example: `https://my-api.my-domain.com`


When you run your app, access to the `/stuff` endpoint would be restricted to authenticated users
whose access tokens carried the permission scope "read:stuff".

For a step-by-step walk-through of how to set up Auth0 for the minimal example, see the
["Getting Started with Auth0"](../tutorials/getting_started_with_auth0) page.

The above code can be found in [examples/basic.py](https://github.com/omnivector-solutions/armasec/blob/main/examples/basic.py>).
