import os

import dotenv
import snick
import typer
from loguru import logger

from armasec.managers import AsymmetricManager
from armasec.exceptions import ArmadaSecurityError

dotenv.load_dotenv()

cli = typer.Typer()


@cli.command()
def decode(
    header_value: str = typer.Argument(
        ...,
        help="The header value (starting with '{AsymmetricManager.auth_scheme}'",
    ),
    secret: str = typer.Option(
        os.environ.get("ARMASEC_SECRET"),
        help="The secret for checking the token signature",
    ),
    algorithm: str = typer.Argument(
        os.environ.get("ARMASEC_ALGORITHM"),
        help="The algorithm to use for checking the token signature",
    ),
    client_id: str = typer.Argument(
        os.environ.get("ARMASEC_CLIENT_ID"),
        help="The unique identifier for the client",
    ),
    domain: str = typer.Argument(
        os.environ.get("ARMASEC_DOMAIN"),
        help="The domain to use for retrieving JWKs",
    ),
    audience: str = typer.Argument(
        os.environ.get("ARMASEC_AUDIENCE"),
        help="The domain to use for retrieving JWKs",
    ),
):
    logger.debug("Constructing manager")
    manager = AsymmetricManager(
        secret,
        algorithm,
        client_id,
        domain,
        audience,
        debug_logger=logger.debug,
    )

    logger.debug("Extracting token:")
    with ArmadaSecurityError.handle_errors(
        "Couldn't extract token payload",
        do_except=manager.log_error,
    ):
        token_payload = manager.extract_token_payload({
            manager.header_key: header_value,
        })
        logger.info(f"Decoded token as: {snick.pretty_format(token_payload.dict())}")


if __name__ == '__main__':
    cli()
