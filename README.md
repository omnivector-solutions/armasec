[contributors-url]: https://github.com/omnivector-solutions/armasec/graphs/contributors
[forks-url]: https://github.com/omnivector-solutions/armasec/network/members
[stars-url]: https://github.com/omnivector-solutions/armasec/stargazers
[issues-url]: https://github.com/omnivector-solutions/armasec/issues
[license-url]: https://github.com/omnivector-solutions/armasec/blob/master/LICENSE
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
  <a href="https://github.com/omnivector-solutions/armasec">
    <img src=".images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">armasec</h3>

  <p align="center">
    A security package that works with OIDC platforms for FastAPI apps.
    <br />
    <a href="https://github.com/omnivector-solutions/armasec/issues">Report Bug</a>
    ·
    <a href="https://github.com/omnivector-solutions/armasec/issues">Request Feature</a>
  </p>
</p>

# Armasec

## Table of Contents

- [Table of Contents](#table-of-contents)
- [About The Project](#about-the-project)
- [Installation](#installation-backend)
- [Example Usage](#example-usage)
- [License](#license)
- [Contact](#contact)


## About The Project

The `armasec` package provides tools to authenticate and authorize requests in a FastAPI
app.  The `TokenSecurity` module can be used with FastAPI's dependency injection to make adding
security to endpoints very simple.

The `armasec` package was built specifically for use with Auth0, but any OIDC complient
platform should work with it as well.

Though `armasec` provides everything you need to apply security, you will still need to
manage users and permissions through the OIDC platform itself.


### Supported algorithms

The `armasec` package supports the following algorithms for authentication:

* HS256: Symmetric secret key based signature checking
* RS256: Asymmetric public/private key based signature checking


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


## Contact
Omnivector Solutions - [www.omnivector.solutions][website] - <info@omnivector.solutions>

Project Link: [https://github.com/omnivector-solutions/armasec](https://github.com/omnivector-solutions/armasec)
