from __future__ import annotations

from time import sleep
from typing import cast

import snick
from jose.exceptions import ExpiredSignatureError
from loguru import logger
from jose import jwt
from pydantic import ValidationError

from armasec_cli.exceptions import Abort, ArmasecCliError
from armasec_cli.schemas import DeviceCodeData, TokenSet, IdentityData
from armasec_cli.cache import load_tokens_from_cache, save_tokens_to_cache
from armasec_cli.client import make_request
from armasec_cli.config import OidcProvider
from armasec_cli.schemas import Persona, CliContext
from armasec_cli.format import terminal_message
from armasec_cli.time_loop import TimeLoop


def extract_persona(token_set: TokenSet | None = None):
    if token_set is None:
        token_set = load_tokens_from_cache()

    try:
        identity_data = validate_token_and_extract_identity(token_set)
    except ExpiredSignatureError:
        Abort.require_condition(
            token_set.refresh_token is not None,
            "The auth token is expired. Please retrieve a new and log in again.",
            raise_kwargs=dict(
                subject="Expired access token",
            ),
        )

        logger.debug("The access token is expired. Attempting to refresh token")
        refresh_access_token(token_set)
        identity_data = validate_token_and_extract_identity(token_set)

    logger.debug(f"Persona created with identity_data: {identity_data}")

    save_tokens_to_cache(token_set)

    return Persona(
        token_set=token_set,
        identity_data=identity_data,
    )


def validate_token_and_extract_identity(token_set: TokenSet) -> IdentityData:
    logger.debug("Validating access token")

    token_file_is_empty = not token_set.access_token
    if token_file_is_empty:
        logger.debug("Access token file exists but it is empty")
        raise Abort(
            """
            Access token file exists but it is empty.

            Please try logging in again.
            """,
            subject="Empty access token file",
            log_message="Empty access token file",
        )

    with Abort.handle_errors(
        """
        There was an unknown error while validating the access token.

        Please try logging in again.
        """,
        ignore_exc_class=ExpiredSignatureError,  # Will be handled in calling context
        raise_kwargs=dict(
            subject="Invalid access token",
            log_message="Unknown error while validating access access token",
        ),
    ):
        token_data = jwt.decode(
            token_set.access_token,
            None,
            options=dict(
                verify_signature=False,
                verify_aud=False,
                verify_exp=True,
            ),
        )

    logger.debug("Extracting identity data from the access token")
    with Abort.handle_errors(
        """
        There was an error extracting the user's identity from the access token.

        Please try logging in again.
        """,
        handle_exc_class=ValidationError,
        raise_kwargs=dict(
            subject="Missing user data",
            log_message="Token data could not be extracted to identity",
        ),
    ):
        identity = IdentityData(
            email=token_data.get("email"),
            client_id=token_data.get("azp"),
        )

    return identity


def init_persona(ctx: CliContext, token_set: TokenSet | None = None):
    if token_set is None:
        token_set = load_tokens_from_cache()

    try:
        identity_data = validate_token_and_extract_identity(token_set)
    except ExpiredSignatureError:
        Abort.require_condition(
            token_set.refresh_token is not None,
            "The auth token is expired. Please retrieve a new and log in again.",
            raise_kwargs=dict(
                subject="Expired access token",
            ),
        )

        logger.debug("The access token is expired. Attempting to refresh token")
        refresh_access_token(ctx, token_set)
        identity_data = validate_token_and_extract_identity(token_set)

    logger.debug(f"Persona created with identity_data: {identity_data}")

    save_tokens_to_cache(token_set)

    return Persona(
        token_set=token_set,
        identity_data=identity_data,
    )


def refresh_access_token(ctx: CliContext, token_set: TokenSet):
    """
    Attempt to fetch a new access token given a refresh token in a token_set.

    Sets the access token in-place.

    If refresh fails, notify the user that they need to log in again.
    """
    print("MAKE THIS FUCKING THING USE THE BASE URL")
    url = "/protocol/openid-connect/token"
    logger.debug(f"Requesting refreshed access token from {url}")

    refreshed_token_set: TokenSet = cast(
        TokenSet,
        make_request(
            ctx.client,
            "/protocol/openid-connect/token",
            "POST",
            abort_message="The auth token could not be refreshed. Please try logging in again.",
            abort_subject="EXPIRED ACCESS TOKEN",
            response_model_cls=TokenSet,
            data=dict(
                client_id=ctx.settings.oidc_client_id,
                audience=ctx.settings.oidc_audience,
                grant_type="refresh_token",
                refresh_token=token_set.refresh_token,
            ),
        ),
    )

    token_set.access_token = refreshed_token_set.access_token


def fetch_auth_tokens(ctx: CliContext) -> TokenSet:
    """
    Fetch an access token (and possibly a refresh token) from Auth0.

    Prints out a URL for the user to use to authenticate and polls the token endpoint to fetch it
    when the browser-based process finishes.
    """
    if ctx.settings.oidc_provider == OidcProvider.KEYCLOAK:
        device_path = "/protocol/openid-connect/auth/device"
        token_path = "/protocol/openid-connect/token"
    elif ctx.settings.oidc_provider == OidcProvider.AUTH0:
        device_path = "/oauth/device/code"
        token_path = "oauth/token"
    else:
        raise ArmasecCliError("Unsupported OIDC Provider.")

    device_code_data: DeviceCodeData = cast(
        DeviceCodeData,
        make_request(
            ctx.client,
            device_path,
            "POST",
            expected_status=200,
            abort_message=(
                """
                There was a problem retrieving a device verification code from
                the auth provider
                """
            ),
            abort_subject="COULD NOT RETRIEVE TOKEN",
            response_model_cls=DeviceCodeData,
            data=dict(
                client_id=ctx.settings.oidc_client_id,
                grant_type="client_credentials",
                audience=ctx.settings.oidc_audience,
            ),
        ),
    )

    max_poll_time = 5 * 60  # 5 minutes
    terminal_message(
        f"""
        To complete login, please open the following link in a browser:

          {device_code_data.verification_uri_complete}

        Waiting up to {max_poll_time / 60} minutes for you to complete the process...
        """,
        subject="Waiting for login",
    )

    for tick in TimeLoop(
        ctx.settings.oidc_max_poll_time,
        message="Waiting for web login",
    ):
        response_data: dict = cast(
            dict,
            make_request(
                ctx.client,
                token_path,
                "POST",
                abort_message=snick.unwrap(
                    """
                    There was a problem retrieving a device verification code
                    from the auth provider
                    """
                ),
                abort_subject="COULD NOT FETCH ACCESS TOKEN",
                data=dict(
                    grant_type="urn:ietf:params:oauth:grant-type:device_code",
                    device_code=device_code_data.device_code,
                    client_id=ctx.settings.oidc_client_id,
                ),
            ),
        )
        if "error" in response_data:
            if response_data["error"] == "authorization_pending":
                logger.debug(f"Token fetch attempt #{tick.counter} failed")
                logger.debug(f"Will try again in {device_code_data.interval} seconds")
                sleep(device_code_data.interval)
            else:
                # TODO: Test this failure condition
                raise Abort(
                    snick.unwrap(
                        """
                        There was a problem retrieving a device verification code
                        from the auth provider:
                        Unexpected failure retrieving access token.
                        """
                    ),
                    subject="Unexpected error",
                    log_message=f"Unexpected error response: {response_data}",
                )
        else:
            return TokenSet(**response_data)

    raise Abort(
        "Login process was not completed in time. Please try again.",
        subject="Timed out",
        log_message="Timed out while waiting for user to complete login",
    )
