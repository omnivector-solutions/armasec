import sys

from loguru import logger


def init_logs(verbose=False):
    logger.remove()

    if verbose:
        logger.add(sys.stdout, level="DEBUG")

    logger.debug("Logging initialized")
