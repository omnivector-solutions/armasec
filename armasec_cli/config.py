import json
from functools import wraps
from pathlib import Path

import snick
import typer
from auto_name_enum import AutoNameEnum, auto
from loguru import logger
from pydantic import BaseModel, ValidationError

from armasec_cli.exceptions import Abort

cache_dir: Path = Path.home() / ".local/share/armasec-cli"
settings_path = cache_dir / "armasec.json"


class OidcProvider(AutoNameEnum):
    AUTH0 = auto()
    KEYCLOAK = auto()


class Settings(BaseModel):
    oidc_domain: str
    oidc_audience: str
    oidc_client_id: str
    oidc_use_https: bool = True
    oidc_max_poll_time: int = 5 * 60  # 5 minutes
    oidc_provider: OidcProvider = OidcProvider.KEYCLOAK


def init_settings(**settings_values):
    try:
        logger.debug("Validating settings")
        return Settings(**settings_values)
    except ValidationError as err:
        raise Abort(
            snick.conjoin(
                "A configuration error was detected.",
                "",
                "Details:",
                "",
                f"[red]{err}[/red]",
            ),
            subject="Configuration Error",
            log_message="Configuration error",
        )


def attach_settings(func):
    @wraps(func)
    def wrapper(ctx: typer.Context, *args, **kwargs):
        try:
            logger.debug(f"Loading settings from {settings_path}")
            settings_values = json.loads(settings_path.read_text())
        except FileNotFoundError:
            raise Abort(
                f"""
                No settings file found at {settings_path}!

                Run the set-config sub-command first to establish your OIDC settings.
                """,
                subject="Settings file missing!",
                log_message="Settings file missing!",
            )
        logger.debug("Binding settings to CLI context")
        ctx.obj.settings = init_settings(**settings_values)
        return func(ctx, *args, **kwargs)

    return wrapper


def dump_settings(settings: Settings):
    logger.debug(f"Saving settings to {settings_path}")
    settings_values = json.dumps(settings.model_dump())
    settings_path.write_text(settings_values)


def clear_settings():
    logger.debug(f"Removing saved settings at {settings_path}")
    settings_path.unlink(missing_ok=True)
