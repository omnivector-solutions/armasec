from __future__ import annotations

from pathlib import Path
from functools import wraps

from loguru import logger

from armasec_cli.schemas import TokenSet
from armasec_cli.exceptions import Abort
from armasec_cli.config import cache_dir


def init_cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            cache_dir.mkdir(exist_ok=True, parents=True)
            token_dir = cache_dir / "token"
            token_dir.mkdir(exist_ok=True)
            info_file = cache_dir / "info.txt"
            info_file.write_text("This directory is used by Armasec CLI for its cache.")
        except Exception:
            raise Abort(
                """
                Cache directory {cache_dir} doesn't exist, is not writable, or could not be created.

                Please check your home directory permissions and try again.
                """,
                subject="Non-writable cache dir",
                log_message="Non-writable cache dir",
            )
        return func(*args, **kwargs)

    return wrapper


def _get_token_paths() -> tuple[Path, Path]:
    token_dir = cache_dir / "token"
    access_token_path: Path = token_dir / "access.token"
    refresh_token_path: Path = token_dir / "refresh.token"
    return (access_token_path, refresh_token_path)


def load_tokens_from_cache() -> TokenSet:
    """
    Loads an access token (and a refresh token if one exists) from the cache.
    """
    (access_token_path, refresh_token_path) = _get_token_paths()

    Abort.require_condition(
        access_token_path.exists(),
        "Please login with your auth token first using the `armasec login` command",
        raise_kwargs=dict(subject="You need to login"),
    )

    logger.debug("Retrieving access token from cache")
    token_set: TokenSet = TokenSet(access_token=access_token_path.read_text())

    if refresh_token_path.exists():
        logger.debug("Retrieving refresh token from cache")
        token_set.refresh_token = refresh_token_path.read_text()

    return token_set


def save_tokens_to_cache(token_set: TokenSet):
    """
    Saves tokens from a token_set to the cache.
    """
    (access_token_path, refresh_token_path) = _get_token_paths()

    logger.debug(f"Caching access token at {access_token_path}")
    access_token_path.write_text(token_set.access_token)
    access_token_path.chmod(0o600)

    if token_set.refresh_token is not None:
        logger.debug(f"Caching refresh token at {refresh_token_path}")
        refresh_token_path.write_text(token_set.refresh_token)
        refresh_token_path.chmod(0o600)


def clear_token_cache():
    """
    Clears the token cache.
    """
    logger.debug("Clearing cached tokens")
    (access_token_path, refresh_token_path) = _get_token_paths()

    logger.debug(f"Removing access token at {access_token_path}")
    if access_token_path.exists():
        access_token_path.unlink()

    logger.debug(f"Removing refresh token at {refresh_token_path}")
    if refresh_token_path.exists():
        refresh_token_path.unlink()
