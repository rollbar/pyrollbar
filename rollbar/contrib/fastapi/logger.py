__all__ = ['LoggerMiddleware']

import logging
import sys

from rollbar.contrib.starlette.logger import LoggerMiddleware as StarletteLoggerMiddleware

log = logging.getLogger(__name__)

if sys.version_info < (3, 7):
    log.error('LoggerMiddleware requires Python 3.7')
    raise RuntimeError('LoggerMiddleware requires Python 3.7')


class LoggerMiddleware(StarletteLoggerMiddleware):
    ...
