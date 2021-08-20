[contributors-url]: https://github.com/omnivector-solutions/armada-security/graphs/contributors
[forks-url]: https://github.com/omnivector-solutions/armada-security/network/members
[stars-url]: https://github.com/omnivector-solutions/armada-security/stargazers
[issues-url]: https://github.com/omnivector-solutions/armada-security/issues
[license-url]: https://github.com/omnivector-solutions/armada-security/blob/master/LICENSE
[website]: https://www.omnivector.solutions
[infrastructure]: https://github.com/omnivector-solutions/infrastructure

[Contributors][contributors-url] •
[Forks][forks-url] •
[Stargazers][stars-url] •
[Issues][issues-url] •
[MIT License][license-url] •
[Website][website]

<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/omnivector-solutions/armada-security">
    <img src=".images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">armada-security</h3>

  <p align="center">
    A security package that works with OIDC platforms for FastAPI apps.
    <br />
    <a href="https://github.com/omnivector-solutions/armada-security/issues">Report Bug</a>
    ·
    <a href="https://github.com/omnivector-solutions/armada-security/issues">Request Feature</a>
  </p>
</p>

[![](https://github.com/omnivector-solutions/armada-security/workflows/TestBuildReleaseEdge/badge.svg)](https://github.com/omnivector-solutions/armada-security-simulator/actions?query=workflow%3ATestBuildReleaseEdge)

# Armada Security

## Table of Contents

- [Table of Contents](#table-of-contents)
- [About The Project](#about-the-project)
- [Installation](#installation-backend)
- [Example Usage](#example-usage)
- [License](#license)
- [Contact](#contact)


## About The Project

The `armada-security` package provides tools to authenticate and authorize request in a FastAPI app.
The `TokenSecurity` module can be used with FastAPI's dependency injection to make adding security
to endpoints very simple.

The `armada-security` package was built specifically for use with Auth0, but any OIDC complient
platform should work with it as well.

Though `armada-security` provides everything you need to apply security, you will still need to
manage users and permissions through the OIDC platform itself.


## Installation

The `armada-security` package can be installed like any other python package. For now, though, it
is only hosted on OmniVector's internal package index at pypicloud.omnivector.solutions.


### Poetry

To install via poetry, you need to add the following section to `pyproject.toml`

```
[[tool.poetry.source]]
name = "pypicloud"
url = "https://pypicloud.omnivector.solutions/simple"
```

Then run:
```
poetry add armada-security
```


### Pip

To install directly with `pip`, you can use the `--index-url` command line argument:

```
pip install --index-url=https://pypicloud.omnivector.solutions/simple armada-security
```


## Example Usage

```
from armasec import TokenManager, TokenSecurity, TokenPayload
from fastapi import FastAPI, Depends
from pydantic import BaseModel


app = FastAPI()

manager = TokenManager(
    secret="supertopsecret",
    algorithm="HS256",
    issuer="https://issuer-url.com/",
    audience="https://audience-url.com",
)
read_stuff_security = TokenSecurity(manager, scopes=["read:stuff"])

@app.get("/stuff")
async def get_items(token_payload: TokenPayload = Depends(read_stuff_security)):
    return dict(
        message="Successfully authenticated!",
        token_payload=token_payload,
    )
```


## License
Distributed under the MIT License. See `LICENSE` for more information.


## Contact
Omnivector Solutions - [www.omnivector.solutions][website] - <info@omnivector.solutions>

Project Link: [https://github.com/omnivector-solutions/armada-security](https://github.com/omnivector-solutions/armada-security)
