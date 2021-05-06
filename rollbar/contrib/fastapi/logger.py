__all__ = ['LoggerMiddleware']

import logging

from rollbar.contrib.starlette import LoggerMiddleware as StarletteLoggerMiddleware

log = logging.getLogger(__name__)


class LoggerMiddleware(StarletteLoggerMiddleware):
    ...
