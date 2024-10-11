from __future__ import annotations


import jose
import pyperclip
import snick
import typer

from armasec_cli.exceptions import Abort, handle_abort
from armasec_cli.schemas import TokenSet, Persona, CliContext
from armasec_cli.cache import init_cache, load_tokens_from_cache, clear_token_cache
from armasec_cli.format import terminal_message, render_json
from armasec_cli.auth import fetch_auth_tokens, extract_persona
from armasec_cli.config import (
    OidcProvider,
    attach_settings,
    init_settings,
    dump_settings,
    clear_settings,
)
from armasec_cli.client import attach_client
from armasec_cli.logging import init_logs


app = typer.Typer()


@app.callback(invoke_without_command=True)
@handle_abort
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, help="Enable verbose logging to the terminal"),
):
    """
    Welcome to the Armasec CLI!

    More information can be shown for each command listed below by running it with the
    --help option.
    """

    if ctx.invoked_subcommand is None:
        terminal_message(
            snick.conjoin(
                "No command provided. Please check [bold magenta]usage[/bold magenta]",
                "",
                f"[yellow]{ctx.get_help()}[/yellow]",
            ),
            subject="Need an Armasec command",
        )
        raise typer.Exit()

    init_logs(verbose=verbose)
    ctx.obj = CliContext()


@app.command()
@handle_abort
@init_cache
@attach_settings
@attach_client
def login(ctx: typer.Context):
    token_set: TokenSet = fetch_auth_tokens(ctx.obj)
    persona: Persona = extract_persona(token_set)
    terminal_message(
        f"User was logged in with email '{persona.identity_data.email}'",
        subject="Logged in!",
    )


@app.command()
@handle_abort
@init_cache
def logout():
    """
    Logs out of the jobbergate-cli. Clears the saved user credentials.
    """
    clear_token_cache()
    terminal_message(
        "User was logged out.",
        subject="Logged out",
    )


@app.command()
@init_cache
def set_config(
    domain: str = typer.Option(..., help="The domain used by your OIDC provider"),
    audience: str = typer.Option(
        None,
        help="The audience required by your OIDC provider",
    ),
    client_id: str = typer.Option(
        ...,
        help="The unique client ID to use for logging in via CLI",
    ),
    use_https: bool = typer.Option(True, help="Use https for requests"),
    max_poll_time: int = typer.Option(
        5 * 60,
        help="The max time to wait for login to complete",
    ),
    provider: OidcProvider = typer.Option(
        OidcProvider.KEYCLOAK,
        help="The OIDC provider you use",
    ),
):
    settings = init_settings(
        oidc_domain=domain,
        oidc_audience=audience,
        oidc_client_id=client_id,
        oidc_use_https=use_https,
        oidc_max_poll_time=max_poll_time,
        oidc_provider=provider,
    )
    dump_settings(settings)


@app.command()
@handle_abort
@init_cache
@attach_settings
def show_config(ctx: typer.Context):
    """
    Show the current config.
    """
    render_json(ctx.obj.settings.model_dump())


@app.command()
@handle_abort
@init_cache
def clear_config():
    """
    Show the current config.
    """
    clear_settings()


@app.command()
@handle_abort
@init_cache
def show_token(
    plain: bool = typer.Option(
        False,
        help="Show the token in plain text.",
    ),
    refresh: bool = typer.Option(
        False,
        help="Show the refresh token instead of the access token.",
    ),
    show_prefix: bool = typer.Option(
        False,
        "--prefix",
        help="Include the 'Bearer' prefix in the output.",
    ),
    show_header: bool = typer.Option(
        False,
        "--header",
        help="Show the token as it would appear in a request header.",
    ),
    decode: bool = typer.Option(
        False,
        "--decode",
        help="Show the content of the decoded access token.",
    ),
):
    """
    Show the token for the logged in user.

    Token output is automatically copied to your clipboard.
    """
    token_set: TokenSet = load_tokens_from_cache()
    token: str | None = None
    if not refresh:
        token = token_set.access_token
        subject = "Access Token"
        Abort.require_condition(
            token is not None,
            "User is not logged in. Please log in first.",
            raise_kwargs=dict(
                subject="Not logged in",
            ),
        )
    else:
        token = token_set.refresh_token
        subject = "Refresh Token"
        Abort.require_condition(
            token is not None,
            snick.unwrap(
                """
                User is not logged in or does not have a refresh token.
                Please try loggin in again.
                """
            ),
            raise_kwargs=dict(
                subject="No refresh token",
            ),
        )

    if decode:
        # Decode the token with ALL verification turned off (we just want to unpack it)
        content = jose.jwt.decode(
            token,
            "secret-will-be-ignored",
            options=dict(
                verify_signature=False,
                verify_aud=False,
                verify_iat=False,
                verify_exp=False,
                verify_nbf=False,
                verify_iss=False,
                verify_sub=False,
                verify_jti=False,
                verify_at_hash=False,
            ),
        )
        render_json(content)
        return

    if show_header:
        token_text = f"""{{ "Authorization": "Bearer {token}" }}"""
    else:
        prefix = "Bearer " if show_prefix else ""
        token_text = f"{prefix}{token}"

    try:
        pyperclip.copy(token_text)
        on_clipboard = True
    except Exception:
        on_clipboard = False

    if plain:
        print(token_text)
    else:
        kwargs = dict(subject=subject, indent=False)
        if on_clipboard:
            kwargs["footer"] = "The output was copied to your clipboard"

        terminal_message(token_text, **kwargs)
