[![Build Status](https://github.com/omnivector-solutions/armasec/actions/workflows/test_on_push.yaml/badge.svg)](https://github.com/omnivector-solutions/armasec/actions/workflows/test_on_push.yaml)
[![Build Documentation](https://github.com/omnivector-solutions/armasec/actions/workflows/build_docs.yaml/badge.svg)](https://github.com/omnivector-solutions/armasec/actions/workflows/build_docs.yaml)


![Python Versions](https://img.shields.io/pypi/pyversions/armasec?label=python-versions&logo=python&style=plastic)
![PyPI Versions](https://img.shields.io/pypi/v/armasec?label=pypi-version&logo=python&style=plastic)
![License](https://img.shields.io/pypi/l/armasec?style=plastic)


> An [Omnivector](https://www.omnivector.io/) initiative
>
> [![omnivector-logo](https://omnivector-public-assets.s3.us-west-2.amazonaws.com/branding/omnivector-logo-text-black-horz.png)](https://www.omnivector.io/)



# Armasec

Adding a security layer on top of your API can be difficult, especially when working with an OIDC
platform. It's hard enough to get your OIDC provider configured correctly. Armasec aims to take the
pain out of securing your APIs routes.

Armasec is an opinionated library that attempts to use the most obvious and commonly used workflows
when working with OIDC and making configuration as simple as possible.

When using the
[Armasec](https://github.com/omnivector-solutions/armasec/blob/main/armasec/armasec.py) helper
class, you only need two configuration settings to get going:

1. Domain: the domain of your OIDC provider
2. Audience: An optional setting that restricts tokens to those intended for your API.

That's it! Once you have those settings dialed in, you can just worry about checking the permissions
scopes of your endpoints


## Documentation

Documentation is hosted hosted on `github.io` at
[the Armasec homepage](https://omnivector-solutions.github.io/armasec/).


## Quickstart

1. Install `armasec` and `uvicorn`:

```bash
pip install armasec uvicorn
```


2. Save th Minimal Example (example.py) locally:

```python
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


4. Set the Armasec environment variables:

* ARMASEC_DOMAIN
* ARMASEC_AUDIENCE


5. Run the app

```bash
uvicorn --host 0.0.0.0 example:app
```


## License

Distributed under the MIT License. See `LICENSE` for more information.
