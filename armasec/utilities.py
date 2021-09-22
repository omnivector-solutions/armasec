"""
Provides some utility functions.
"""
from traceback import format_tb
from types import TracebackType
from typing import Callable

from snick import dedent


def noop(*args, **kwargs):
    """
    This is a no-op function that...does nothing.
    """
    pass


def log_error(
    logger: Callable[..., None], err: Exception, final_message: str, trace: TracebackType
):
    """
    Logs an en error with the supplied message, a string representation of the error, and its
    traceback. If the logger supplied is noop, do nothing. Pass as a partial when using the Buzz
    `handle_errors` context manager::

        with Buzz.handle_errors("Boom!", do_except=partial(log_error, debug_logger)):
            do_some_risky_stuff()
    """
    if logger is noop:
        return

    message_template = dedent(
        """
        {final_message}

        Error:
        ______
        {err}

        Traceback:
        ----------
        {trace}
    """
    )

    logger(
        message_template.format(
            final_message=final_message,
            err=str(err),
            trace="\n".join(format_tb(trace)),
        )
    )
