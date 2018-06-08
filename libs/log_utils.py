import logging
import sys

getLogger = logging.getLogger


class _NullHandler(logging.Handler):
    """No-op logging handler to avoid unexpected logging warnings."""

    def emit(self, record):
        pass

_NULL_HANDLER = _NullHandler()
_DULWICH_LOGGER = getLogger('gitserver')
_DULWICH_LOGGER.addHandler(_NULL_HANDLER)


def default_logging_config():
    """Set up the default Dulwich loggers."""
    remove_null_handler()
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format='%(asctime)s %(levelname)s: %(message)s')


def remove_null_handler():
    """Remove the null handler from the Dulwich loggers.

    If a caller wants to set up logging using something other than
    default_logging_config, calling this function first is a minor optimization
    to avoid the overhead of using the _NullHandler.
    """
    _DULWICH_LOGGER.removeHandler(_NULL_HANDLER)
