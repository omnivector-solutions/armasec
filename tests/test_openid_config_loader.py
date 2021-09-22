"""
Test the openid_config_loader module.
"""
from unittest import mock

import httpx
import pytest
import respx
import starlette

from armasec.exceptions import AuthenticationError
from armasec.openid_config_loader import OpenidConfigLoader
from armasec.schemas import JWKs


def test_config__is_lazy_loaded(rs256_domain, mock_openid_server):
    """
    Verify that the config property lazy loads from the openid-configuration route.
    """
    OpenidConfigLoader(rs256_domain)
    assert not mock_openid_server.openid_config_route.called


def test_build_openid_config_url():
    """
    Verify that the openid config url is built correctly.
    """
    assert (
        OpenidConfigLoader.build_openid_config_url("my.domain")
        == "https://my.domain/.well-known/openid-configuration"
    )


def test__load_openid_resource__success(mock_openid_server):
    """
    Verify that the helper method can fetch json data via a GET call to a url.
    """
    loader = OpenidConfigLoader("my.domain")
    with respx.mock:
        route = respx.get("https://my.domain/blah")
        route.return_value = httpx.Response(
            starlette.status.HTTP_200_OK,
            json=dict(foo="bar"),
        )
        assert loader._load_openid_resource("https://my.domain/blah") == dict(foo="bar")


def test__load_openid_resource__fails_on_failed_request(mock_openid_server):
    """
    Verify that the helper method throws an exception if the GET request fails.
    """
    loader = OpenidConfigLoader("my.domain")
    with mock.patch("httpx.get", side_effect=Exception("BOOM!")):
        with pytest.raises(AuthenticationError, match="Call to url .* failed"):
            loader._load_openid_resource("https://my.domain/blah")


def test__load_openid_resource__fails_on_bad_status_code(mock_openid_server):
    """
    Verify that the helper method throws an exception if the response status code is not OK.
    """
    loader = OpenidConfigLoader("my.domain")
    with respx.mock:
        route = respx.get("https://my.domain/blah")
        route.return_value = httpx.Response(starlette.status.HTTP_400_BAD_REQUEST)
        with pytest.raises(AuthenticationError, match="Didn't get a success status code"):
            loader._load_openid_resource("https://my.domain/blah")


def test_config__success(mock_openid_server, rs256_openid_config, rs256_domain):
    """
    Verify that the config property successfully loads a config from the server. Also verify that
    it will re-use the lazy-loaded config on subsequent calls.
    """
    loader = OpenidConfigLoader(rs256_domain)
    config = loader.config
    assert config.issuer == rs256_openid_config.issuer
    assert config.jwks_uri == rs256_openid_config.jwks_uri
    assert mock_openid_server.openid_config_route.called

    loader.config
    assert mock_openid_server.openid_config_route.call_count == 1


def test_config__fail_on_invalid_config(mock_openid_server, rs256_openid_config, rs256_domain):
    """
    Verify that the config property throws an exception if the loaded config was invalid.
    """
    loader = OpenidConfigLoader(rs256_domain)
    mock_openid_server.openid_config_route.return_value = httpx.Response(
        starlette.status.HTTP_200_OK,
        json=dict(bad="data"),
    )
    with pytest.raises(AuthenticationError, match="openid config data was invalid"):
        loader.config


def test_jwks__success(mock_openid_server, rs256_jwk, rs256_domain):
    """
    Verify that the jwks property successfully loads jwks from the server. Also verify that
    it will re-use the lazy-loaded jwks on subsequent calls.
    """
    loader = OpenidConfigLoader(rs256_domain)
    jwks = loader.jwks
    assert jwks == JWKs(keys=[rs256_jwk])
    assert mock_openid_server.jwks_route.called

    loader.jwks
    assert mock_openid_server.jwks_route.call_count == 1


def test_jwks__fail_on_invalid_jwks(mock_openid_server, rs256_jwk, rs256_domain):
    """
    Verify that the config property throws an exception if the loaded config was invalid.
    """
    loader = OpenidConfigLoader(rs256_domain)
    mock_openid_server.jwks_route.return_value = httpx.Response(
        starlette.status.HTTP_200_OK,
        json=dict(bad="data"),
    )
    with pytest.raises(AuthenticationError, match="jwks data was invalid"):
        loader.jwks
