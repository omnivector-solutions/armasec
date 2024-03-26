import json
from pathlib import Path

import pytest
from typer import Context

from armasec_cli.exceptions import Abort
from armasec_cli.schemas import CliContext
from armasec_cli.config import init_settings, attach_settings, dump_settings


def test_init_settings__success():
    settings = init_settings(
        oidc_domain="test.domain",
        oidc_audience="https://test.domain/api",
        oidc_client_id="test-client-id",
    )
    assert settings.oidc_domain == "test.domain"
    assert settings.oidc_audience == "https://test.domain/api"
    assert settings.oidc_client_id == "test-client-id"


def test_init_settings__raises_Abort_on_invalid_config():
    with pytest.raises(Abort):
        init_settings()


def test_dump_settings__success(tmp_path, mocker):
    dummy_settings_path = tmp_path / "settings.json"
    with mocker.patch("armasec_cli.config.settings_path", new=dummy_settings_path):
        dump_settings(
            init_settings(
                oidc_domain="test.domain",
                oidc_audience="https://test.domain/api",
                oidc_client_id="test-client-id",
            )
        )
        settings_dict = json.loads(dummy_settings_path.read_text())

    assert settings_dict["oidc_domain"] == "test.domain"
    assert settings_dict["oidc_audience"] == "https://test.domain/api"
    assert settings_dict["oidc_client_id"] == "test-client-id"


def test_attach_settings__success(tmp_path, mocker, mock_context):
    dummy_settings_path = tmp_path / "settings.json"
    with mocker.patch("armasec_cli.config.settings_path", new=dummy_settings_path):
        dump_settings(
            init_settings(
                oidc_domain="test.domain",
                oidc_audience="https://test.domain/api",
                oidc_client_id="test-client-id",
            )
        )

        @attach_settings
        def _helper(ctx):
            assert ctx.obj.settings.oidc_domain == "test.domain"
            assert ctx.obj.settings.oidc_audience == "https://test.domain/api"
            assert ctx.obj.settings.oidc_client_id == "test-client-id"

        _helper(mock_context)


def test_attach_settings__raises_Abort_if_settings_file_is_not_found(mocker):
    with mocker.patch("armasec_cli.config.settings_path", new=Path("fake-path")):

        @attach_settings
        def _helper(*_):
            pass

        typer_context = Context(mocker.MagicMock())
        typer_context.obj = CliContext()
        with pytest.raises(Abort, match="No settings file found"):
            _helper(typer_context)
