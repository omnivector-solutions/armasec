"""
This module provides a pytest plugin for testing.
"""

from collections import namedtuple
from contextlib import _GeneratorContextManager, contextmanager
from datetime import datetime
from typing import Callable, Optional

import httpx
import pytest
import respx
import starlette
from jose import jwt
from snick import dedent, strip_whitespace

from armasec.openid_config_loader import OpenidConfigLoader
from armasec.schemas.armasec_config import DomainConfig
from armasec.schemas.jwks import JWK, JWKs
from armasec.schemas.openid_config import OpenidConfig


@pytest.fixture()
def rs256_domain():
    """
    Provide a fixture that returns a domain for use in other fixtures.

    The value here doesn't really have anything to do with an actual domain name.
    """
    return "armasec.dev"


@pytest.fixture()
def rs256_domain_config(rs256_domain):
    """
    Provide a fixture that returns the DomainConfig model for the default rs256 domain.

    Args:
        rs256_domain: An implicit fixture parameter.
    """
    return DomainConfig(domain=rs256_domain, audience="https://this.api")


@pytest.fixture()
def rs256_iss(rs256_domain):
    """
    Provide a fixture that returns an issuer claim for use in other fixtures.

    Args:
        rs256_domain: An implicit fixture parameter.
    """
    return f"https://{rs256_domain}"


@pytest.fixture()
def rs256_kid():
    """
    Provide a fixture that returns a KID header value for use in other fixtures.
    """
    return "SAMPLE_KID"


@pytest.fixture()
def rs256_sub():
    """
    Provide a fixture that returns a sum claim for use in other fixtures.
    """
    return "SAMPLE_SUB"


@pytest.fixture()
def rs256_private_key():
    """
    Provide a fixture that returns a pre-generated private key for RS256 hashing in other fixtures.
    """
    return dedent(
        """
        -----BEGIN RSA PRIVATE KEY-----
        MIIEpAIBAAKCAQEAw408+QDZ10idz4ytJtwFQE4YgmrjvCoEXjtTUWQ3H4nWAAYQ
        +oE9xpr/gosNiFMuyRburvXT+Rkq8ry8tWoUzN2zViaarot+Tt9I71sVlnIsbtDZ
        +XrteMvBwjARn/MEAQEwDLvVzrBnAZrOTwrIkznyJttZh7STrt6y5X91i2MMm3xu
        9QK90kpu3rymAyT5V+AEIRzZai/ZT4YfLDutXulOVlWPQ55Xww1mbheGQ99fUMo5
        LmkxM5Jsz8ulIVvq/G/8guiKwAPJN/8S34NbkgL5GoeXT8uNDkbhtkLh5+o2T4EL
        9/ODKHqx46pHgUmBiC6wNv6uJXdH7qpaqhPR3QIDAQABAoIBABeyl/788Wk7bZRn
        UdxxsVk3nZTAa1S0Ks9YlSI56MwzofFiys/wtZHJ2sjxHPS2T+cilk4xkDyRpjjA
        UoYRku+4tjDsgLZCRU49lNMc0KLotyW+vYuUMA8BcjucI6akhomwoSgJ40Em83So
        U/QUNHZTAVtgHZtqcLMyXa+eIJqBcfsMHFkCgSF8LSD/XkRBMm1SREswDw6KqQQ0
        sZ/8TVF9sJTi3/OG8m5OfI+44AYDaMH5wKoOBcR3FBln+dEutB6JuRjmpnEjQpIT
        DggULc+Dzb/c75yhT1qZSEL3Z99JQTbytPm6boNGKmzUE9HCoY84wKfnhUDocFKW
        jnHMmKkCgYEA7/gRAtLjbJW1rbxw8xN3cyOZEJsMFt4mXMmne6nDTttVKb0wUuXJ
        H8prKAXDOzadAZgPeGJXVSNgGoNeNtkmEKDtysrRiZbWiTRxYPE36MrHFGOywjTn
        tP8qMJHmHYkxS16nqrOl0znUWv6Q6/qwd59Utuu4IJF/CxqP3Z6HPssCgYEA0J2M
        1gRgGj8NnGoIKS58gc3Aa5RdqWKoeiyXeN/zRDfMCKpPsVykvZJb4cLcEdcwe9kC
        3xpgIPaTZCPwhJ1rYiZ0/Xr7oIf0E66IeEKs/bchKcT9+sSaWgc5/zQ7aQ/XpwzU
        nKCTTeMGFUyulCIkoe2tLEQ+Mw1OphIXv17fNPcCgYEAjWgVxh81ivgRjiZ8PJEd
        E4lHmmRzVEpmOslN225nO+G9ppHolwD3ardiO7xhllQRYy4S97KjmfT1ncoJy7Jc
        XvImDhlELprnIwT3RtP+STys4ZP6c7yvSZYPa32eJ4t/s9U8YjfooLb0LwbRqW0Z
        bfRC/GOdJfv27Dkjy8muEs8CgYEAo+oHDOonMLg2U54kh2cVQVCPTngnF76DLmv3
        IGym0gUddfmL4Iowjxt+wma/T+1LFSSwUuiAe6YCrX5nr2uZQmeBKOIG8F2idAyB
        Ai0xi7Dmh9FW1kDAHtjqwxEhVS2zfnhgXij1VQ96aiX0TkR9kBYWKV/9l1NvZqF0
        s1MyAoUCgYA0wfJrCTXdWitkyfxApcmoTxt0ljqUwO6F5fhojf8PU1ouglgkRXtm
        1rSDGp7YUfODhWNSsN2P/eaDybcZo+TGtLQJ5Bai3Qxqh8xPaKCsSZbcPRLRP0w5
        CbTvFEyj6EBEH+TJL/Loa4hKFuAk7ErBAtzMCw6LchTjB/OF+dUusA==
        -----END RSA PRIVATE KEY-----
        """
    ).encode("utf-8")


@pytest.fixture()
def rs256_public_key():
    """
    Provide a fixture that returns a pre-generated public key for RS256 hashing in other fixtures.
    """
    return dedent(
        """
        -----BEGIN RSA PUBLIC KEY-----
        MIIBCgKCAQEAw408+QDZ10idz4ytJtwFQE4YgmrjvCoEXjtTUWQ3H4nWAAYQ+oE9
        xpr/gosNiFMuyRburvXT+Rkq8ry8tWoUzN2zViaarot+Tt9I71sVlnIsbtDZ+Xrt
        eMvBwjARn/MEAQEwDLvVzrBnAZrOTwrIkznyJttZh7STrt6y5X91i2MMm3xu9QK9
        0kpu3rymAyT5V+AEIRzZai/ZT4YfLDutXulOVlWPQ55Xww1mbheGQ99fUMo5Lmkx
        M5Jsz8ulIVvq/G/8guiKwAPJN/8S34NbkgL5GoeXT8uNDkbhtkLh5+o2T4EL9/OD
        KHqx46pHgUmBiC6wNv6uJXdH7qpaqhPR3QIDAQAB
        -----END RSA PUBLIC KEY-----
        """
    ).encode("utf-8")


@pytest.fixture()
def rs256_jwk(rs256_kid):
    """
    Provide a fixture that returns a JWK for use in other fixtures.

    Args:
        rs256_kid: An implicit fixture parameter.
    """
    return JWK(
        alg="RS256",
        kty="RSA",
        kid=rs256_kid,
        n=strip_whitespace(
            """
                w408-QDZ10idz4ytJtwFQE4YgmrjvCoEXjtTUWQ3H4nWAAYQ-oE9xpr_gosNiFMuyRburvXT-Rkq8ry8tWoU
                zN2zViaarot-Tt9I71sVlnIsbtDZ-XrteMvBwjARn_MEAQEwDLvVzrBnAZrOTwrIkznyJttZh7STrt6y5X91
                i2MMm3xu9QK90kpu3rymAyT5V-AEIRzZai_ZT4YfLDutXulOVlWPQ55Xww1mbheGQ99fUMo5LmkxM5Jsz8ul
                IVvq_G_8guiKwAPJN_8S34NbkgL5GoeXT8uNDkbhtkLh5-o2T4EL9_ODKHqx46pHgUmBiC6wNv6uJXdH7qpa
                qhPR3Q
            """
        ),
        e="AQAB",
    )


@pytest.fixture()
def build_rs256_token(rs256_private_key, rs256_iss, rs256_sub, rs256_kid):
    """
    Provide a fixture that returns a helper method that can build a JWT.

    The JWT is signed with the private key provided by the rs256_private_key.

    Args:
        rs256_private_key: An implicit fixture parameter.
        rs256_iss:         An implicit fixture parameter.
        rs256_sub:         An implicit fixture parameter.
    """
    base_claims = dict(
        iss=rs256_iss,
        sub=rs256_sub,
        permissions=[],
    )
    base_headers = dict(kid=rs256_kid)

    def _helper(
        claim_overrides: Optional[dict] = None,
        headers_overrides: Optional[dict] = None,
    ):
        """
        Encode a jwt token with the default claims and headers overridden with user supplied values.
        """
        if claim_overrides is None:
            claim_overrides = dict()

        if headers_overrides is None:
            headers_overrides = dict()

        now = int(datetime.utcnow().timestamp())

        return jwt.encode(
            {
                "iat": now,
                "exp": now + 60 * 60,  # expires in an hour from now
                **base_claims,
                **claim_overrides,
            },
            rs256_private_key,
            algorithm="RS256",
            headers={
                **base_headers,
                **headers_overrides,
            },
        )

    return _helper


@pytest.fixture
def rs256_jwks_uri(rs256_domain):
    """
    Provide a fixture that returns a jwks uri for use in other fixtures.

    Args:
        rs256_jwks_uri: An implicit fixture parameter.
    """
    return f"https://{rs256_domain}/.well-known/jwks.json"


@pytest.fixture
def rs256_openid_config(rs256_iss, rs256_jwks_uri):
    """
    Provide a fixture that returns an openid configuration for use in other fixtures.

    Args:
        rs256_iss:      An implicit fixture parameter.
        rs256_jwks_uri: An implicit fixture parameter.
    """
    return OpenidConfig(
        issuer=rs256_iss,
        jwks_uri=rs256_jwks_uri,
    )


def build_mock_openid_server(
    domain, openid_config, jwk, jwks_uri
) -> Callable[[str, OpenidConfig, JWK, str], _GeneratorContextManager]:
    """
    Provide a fixture that returns a context manager that mocks opend-config routes.

    Args:
        domain:        The domain of the openid server to mock.
        openid_config: The config to return from the mocked config route.
        jwk:           The jwk to return from the mocked jwk route.
        jwks_uri:      The URL of the jwks route to mock.

    Returns:
        A context manager that, while active, mocks the openid routes needed by Armasec.
    """

    @contextmanager
    def _helper(
        domain: str = domain,
        openid_config: OpenidConfig = openid_config,
        jwk: JWK = jwk,
        jwks_uri: str = jwks_uri,
    ):
        MockOpenidRoutes = namedtuple("MockOpenidRoutes", ["openid_config_route", "jwks_route"])
        with respx.mock:
            openid_config_route = respx.get(
                OpenidConfigLoader.build_openid_config_url(domain),
            )
            openid_config_route.return_value = httpx.Response(
                starlette.status.HTTP_200_OK,
                json=openid_config.model_dump(mode="json"),
            )

            jwks = JWKs(keys=[jwk])
            jwks_route = respx.get(jwks_uri)
            jwks_route.return_value = httpx.Response(
                starlette.status.HTTP_200_OK,
                json=jwks.model_dump(mode="json"),
            )
            yield MockOpenidRoutes(openid_config_route, jwks_route)

    return _helper


@pytest.fixture
def mock_openid_server(rs256_domain, rs256_openid_config, rs256_jwk, rs256_jwks_uri):
    """
    Provide a fixture that mocks an openid server using the extension fixtures.

    Args:
        rs256_domain:        An implicit fixture parameter.
        rs256_openid_config: An implicit fixture parameter.
        rs256_jwk:           An implicit fixture parameter.
        rs256_jwks_uri:      An implicit fixture parameter.
    """
    builder = build_mock_openid_server(rs256_domain, rs256_openid_config, rs256_jwk, rs256_jwks_uri)
    with builder() as constructed_builder:
        yield constructed_builder
