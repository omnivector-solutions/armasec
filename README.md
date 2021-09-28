![main build](https://img.shields.io/github/workflow/status/omnivector-solutions/armasec/test_on_push/main?label=main-build&logo=github&style=plastic)
![github issues](https://img.shields.io/github/issues/omnivector-solutions/py-buzz?label=issues&logo=github&style=plastic)
![github pull-requests](https://img.shields.io/github/issues-pr/omnivector-solutions/armasec?label=pull-requests&logo=github&style=plastic)
![github contributors](https://img.shields.io/github/contributors/omnivector-solutions/armasec?logo=github&style=plastic)

![python-versions](https://img.shields.io/pypi/pyversions/armasec?label=python-versions&logo=python&style=plastic)
![pypi version](https://img.shields.io/pypi/v/armasec?label=pypi-version&logo=python&style=plastic)

![license](https://img.shields.io/pypi/l/armasec?style=plastic)

# Armasec

A security package that works with OIDC platforms for FastAPI apps.


## About The Project

The `armasec` package provides tools to authenticate and authorize requests in a FastAPI
app using tokens issued by an OpenID Connect (OIDC) provider. It is an opinionated package that
requires minimal configuration.

Although the `armasec` package was built specifically for use with Auth0, any OIDC complient
platform should theoretically work with it as well. Only Auth0 has been tested so far, but other
platform support should follow in subsequent releases.

Though `armasec` provides everything you need to apply security to your FastAPI endpoints, you will
still need to manage users and permissions through the OIDC platform itself.


## Documentation

Documentation is hosted hosted on `github.io` at
[the Armasec homepage](https://omnivector-solutions.github.io/armasec/)


## Installation

The `armasec` package can be installed like any other python package.


### Poetry

To install via poetry, simply run:
```bash
$ poetry add armasec
```


### Pip

To install directly with `pip`, simply run:

```bash
$ pip install armasec
```


## Example Usage

```python
import os

from armasec import Armasec
from fastapi import FastAPI, Depends


app = FastAPI()
armasec = Armasec(os.environ.get("ARMASEC_DOMAIN"), audience=os.environ.get("ARMASEC_AUDIENCE"))

@app.get("/stuff", dependencies=[Depends(armasec.lockdown("read:stuff"))])
async def check_access():
    return dict(message="Successfully authenticated!")
```


## License
Distributed under the MIT License. See `LICENSE` for more information.
