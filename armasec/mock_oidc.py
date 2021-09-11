"""
This module provides a pytest plugin for testing AsymmetricManager.

The settings provided in the MockOpenidServer were generated from a temporary Auth0 instance that
was created expressly to create valid values to test against. This instance was not used for any
other purpose and has already been desposed of. Additionally, no actual connections to Auth0 are
made when using this pytest plugin.

Do NOT use any of the values from this mock server in your own applications.

However, changing the values herein will break functionality in the mock_openid_server fixture.

Example Usage::

    def test_decode(mock_openid_server):
        manager = AsymmetricManager(
            secret=mock_openid_server.client_secret,
            client_id=mock_openid_server.client_id,
            algorithm=mock_openid_server.algorithm,
            domain=mock_openid_server.domain,
            audience=mock_openid_server.audience,
        )
        token_payload = manager.decode(mock_openid_server.access_token)
        assert token_payload.sub == "m1d1F6CmTThowu74diMLAIuNDGok5mLW@clients"
"""

import contextlib
import typing

import httpx
import pytest
import respx
import starlette

from armasec.openid_config import OpenidConfig
from armasec.jwks import JWK, JWKs
from armasec.utilities import build_openid_config_url


class MockOpenidServer:
    domain: str
    audience: str
    client_id: str
    client_secret: str
    algorithm: str
    openid_config: OpenidConfig
    jwks: JWKs
    test_access_token: str
    openid_config_route: typing.Optional[respx.Route]
    jwks_route: typing.Optional[respx.Route]

    def __init__(self):
        self.domain = "dev-0m8jf981.us.auth0.com"
        self.audience = "https://test-server.com"
        self.client_id = "m1d1F6CmTThowu74diMLAIuNDGok5mLW"
        self.client_secret = "v9HiH_X7wmYxqyoF1dR4Jofhb1MCikkA2tgJK7zf23KphiOypmyEaP_NkEHnNkkwa",
        self.algorithm = "RS256"
        self.openid_config = OpenidConfig(
            issuer="https://dev-0m8jf981.us.auth0.com/",
            jwks_uri="https://dev-0m8jf981.us.auth0.com/.well-known/jwks.json",
        )
        self.jwks = JWKs(
            keys=[
                JWK(
                    alg="RS256",
                    kty="RSA",
                    use="sig",
                    n="0szFPJb_WmN8lo1u3ddQPg-XrL0H2H-vUZaf2QXdxHA0YcIi8TSGNohyvJzLr2kMSpEemFkrCnkT6PQW26_VmyR6vJfG8hl3YWAYQ5XeBUq8NlGp64hVYI8gP4488LjLVS9kQlITwYUt9vdUqozU-Oe8o_v9nwqMcEzSgOMAjWf1uCb0m1Llpj5mHZtMQ2dcbH-NQyHJNbHPzoP-_fO41hXUqLZsGnotyVHvPoDZQWHWB7SRipSHAoaUqUMmb0NZvmMc1A4B5_bUqpL1L1M7PUVlcxN6WIfr5ViR3R4U6WIs7C6ltq9VLxDTzNMS_XMbBz7ufLh6ts3N0BLBFTWjgQ",
                    e="AQAB",
                    kid="T0vnJD2jpx4d-tAdLIf5I",
                    x5t="ifBId3awfJfs3OlgAuPA6dXE6n8",
                    x5c=[
                        "MIIDDTCCAfWgAwIBAgIJdrmGLIDPOUGPMA0GCSqGSIb3DQEBCwUAMCQxIjAgBgNVBAMTGWRldi0wbThqZjk4MS51cy5hdXRoMC5jb20wHhcNMjEwODE3MjEyMzU1WhcNMzUwNDI2MjEyMzU1WjAkMSIwIAYDVQQDExlkZXYtMG04amY5ODEudXMuYXV0aDAuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0szFPJb/WmN8lo1u3ddQPg+XrL0H2H+vUZaf2QXdxHA0YcIi8TSGNohyvJzLr2kMSpEemFkrCnkT6PQW26/VmyR6vJfG8hl3YWAYQ5XeBUq8NlGp64hVYI8gP4488LjLVS9kQlITwYUt9vdUqozU+Oe8o/v9nwqMcEzSgOMAjWf1uCb0m1Llpj5mHZtMQ2dcbH+NQyHJNbHPzoP+/fO41hXUqLZsGnotyVHvPoDZQWHWB7SRipSHAoaUqUMmb0NZvmMc1A4B5/bUqpL1L1M7PUVlcxN6WIfr5ViR3R4U6WIs7C6ltq9VLxDTzNMS/XMbBz7ufLh6ts3N0BLBFTWjgQIDAQABo0IwQDAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBQqhH7AmV3+uPURchMBGifLRJ2WGDAOBgNVHQ8BAf8EBAMCAoQwDQYJKoZIhvcNAQELBQADggEBAIS3zV431S0Kv+fELBGvdwW/aAKEid4b2UPD/jsycn1TLKcDpe5Rg7sKcTrOcj2HdM/KSI9Kkq1cvi3h1+2u9vtFMo7rsSwX0CGNdnn6Rshwny2nSd7iYZWpta15cseOemfgTCPR7SLS9mz3uqTXXO22DcUYGPMV6IYDrCy7jAT3V3opJnm/okQnXvoitVs3v1jpSYXhNgbHHzwojrZM4oADUTmeDDNxBucETjyz6u4bSXCMnj3ZPywKCmPrmqwuwmdV/94ECU//X2InXEyqQ3rx0Gzh3OSN6GgTzECzW9Tv/TzYXgtkly1u/Afkd5SeWcjOcGu5wlrH0xaz7iH1Qqk=",
                    ],
                ),
                dict(
                    alg="RS256",
                    kty="RSA",
                    use="sig",
                    n="3BZNeSLaegu3RDoy9MS0mvPF0ZLSJvolpj0Y8EGVK8ELQ5BTq1SUdK1Xwq3HVrbbrPRDa2Q781bk7fCnFxT8h68IueemrEart-3e2DYqDD1jrt1fWAfhfVLQhhHChtg2MsQHb0IjcfzvzPTo4MAwupJ478TbNf7OHEEcMDVTvgtnlKIXFF1PH3jTbK5adxAlXkLH6P5EN4A5yK3LlEc6Wr2LMVm7Pb_yRD0yrrzYdeU6ulkf9FEf3uaDTk0l6EzSpqs5rv_DtJwxISpiomVDhapi4p9ywUyiAfFv3NtZvExO8viAOyORoQnGbjtvzE2Z9Iejy1vB01TtRkxKJBnpQQ",
                    e="AQAB",
                    kid="81BTwiCNFHpCVuNcNiHTX",
                    x5t="vfytnSukTVrsCtHrWD0KTpyYZV8",
                    x5c=[
                        "MIIDDTCCAfWgAwIBAgIJNGRzCjiZl8OGMA0GCSqGSIb3DQEBCwUAMCQxIjAgBgNVBAMTGWRldi0wbThqZjk4MS51cy5hdXRoMC5jb20wHhcNMjEwODE3MjEyMzU2WhcNMzUwNDI2MjEyMzU2WjAkMSIwIAYDVQQDExlkZXYtMG04amY5ODEudXMuYXV0aDAuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3BZNeSLaegu3RDoy9MS0mvPF0ZLSJvolpj0Y8EGVK8ELQ5BTq1SUdK1Xwq3HVrbbrPRDa2Q781bk7fCnFxT8h68IueemrEart+3e2DYqDD1jrt1fWAfhfVLQhhHChtg2MsQHb0IjcfzvzPTo4MAwupJ478TbNf7OHEEcMDVTvgtnlKIXFF1PH3jTbK5adxAlXkLH6P5EN4A5yK3LlEc6Wr2LMVm7Pb/yRD0yrrzYdeU6ulkf9FEf3uaDTk0l6EzSpqs5rv/DtJwxISpiomVDhapi4p9ywUyiAfFv3NtZvExO8viAOyORoQnGbjtvzE2Z9Iejy1vB01TtRkxKJBnpQQIDAQABo0IwQDAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBRNoXttxsoqUQw/qICIxi7QDVuq+DAOBgNVHQ8BAf8EBAMCAoQwDQYJKoZIhvcNAQELBQADggEBAJWHNCaG8PQ5UqZh+ksY7ZvOE9bzQ9txRhPC0txTwaQ27Guq2dCyq5X08oENJ2fSQ1ZlhzatAawsHsqp7hA3drxwRy70crWXA82Od6ogXQp6MfeTEt2/btyJADZ1dXN5lEGaoCOLInxssotq/w2Va+zkNytOthz4dkZzDEDPq5XS64A1ZEGpO2osAqQ1bEprVpaVr00+POFdYFkyPcJWZULOFvJ/YFbwhicOlTyv/6V34RMKs+fPLgV23hO/sndrbXFO18PaXGmiS3HbdHRhSt++IykPh6F0OS7gGHWX0GaKx48zbcWiVOZnJed6bHKip6ldRxH9lPqPqsAGpXpBKfY=",
                    ],
                ),
            ],
        )
        self.access_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IlQwdm5KRDJqcHg0ZC10QWRMSWY1SSJ9.eyJpc3MiOiJodHRwczovL2Rldi0wbThqZjk4MS51cy5hdXRoMC5jb20vIiwic3ViIjoibTFkMUY2Q21UVGhvd3U3NGRpTUxBSXVOREdvazVtTFdAY2xpZW50cyIsImF1ZCI6Imh0dHBzOi8vdGVzdC1zZXJ2ZXIuY29tIiwiaWF0IjoxNjMxMzE1NTYxLCJleHAiOjE2MzE0MDE5NjEsImF6cCI6Im0xZDFGNkNtVFRob3d1NzRkaU1MQUl1TkRHb2s1bUxXIiwiZ3R5IjoiY2xpZW50LWNyZWRlbnRpYWxzIn0.ogBomiHneu2Uh7yXQ-vbRk8pBiUNepUDUDM0yfTo7p5PPfPZyvH_8yQcZzuh1j1aN5sSigHCdDhASFa7y0iJoiAxzvAVIfJgCKNCqv13UKhe5Ptdaw8U55ZFO-JSVb2j9mHknfyJWp9iYoD0RwlsRbThAS3fJTDY9qRCMERdONRmBvx10GcmPOgY-GHYrm22yg3vb77SDjrG4KFqx5vA5lITczaeAIGnFWw7S-K_g6ovyROlfL_0G9dHw5vQfTw_E0ApDtCffXv46B1PVVSKZriPBqpG26pBiNTQlw8m0Hw1TvEZvL8cFDItCQjS0XyHtk30eVRO869971_HHe_8bA"
        self.openid_config_route = None
        self.jwks_route = None

    @contextlib.contextmanager
    def mock(self):
        try:
            with respx.mock:
                self.openid_config_route = respx.get(build_openid_config_url(self.domain))
                self.openid_config_route.return_value = httpx.Response(
                    starlette.status.HTTP_200_OK,
                    json=self.openid_config.dict(),
                )

                self.jwks_route = respx.get(self.openid_config.jwks_uri)
                self.jwks_route.return_value = httpx.Response(
                    starlette.status.HTTP_200_OK,
                    json=self.jwks.dict(),
                )
                yield self
        finally:
            self.openid_config_route = None
            self.jwks_route = None


@pytest.fixture
def mock_openid_server():
    server = MockOpenidServer()
    with server.mock() as mocked:
        yield mocked
