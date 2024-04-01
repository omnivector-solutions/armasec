"""
Hook specification module for armasec plugins.
"""

from typing import Callable

import pluggy
from starlette.requests import Request

from armasec.token_payload import TokenPayload

hookspec = pluggy.HookspecMarker("armasec")


@hookspec
def armasec_plugin_check(
    request: Request,
    token_payload: TokenPayload,
    debug_logger: Callable[..., None],
) -> None:
    """
    Check a token payload for validity against a request using your plugin.

    If the check fails, it should raise a ArmasecError or a subclass thereof.

    Args:
        request:       The original request made to the secured endpoint. Will be passed
                       to the plugin method if the implementation includes it as a
                       keyword argument.
        token_payload: The contents of the auth token. Will be passed ot the plugin
                       method if the implementation includes it as a keyword argument
        debug_logger:  A callable, that if provided, will allow debug logging. Should be
                       passed as a logger method like `logger.debug`. Will be passed to
                       the plugin method if the implementation includes it as a keyword
                       argument.
    """
