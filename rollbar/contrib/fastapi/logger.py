__all__ = ['LoggerMiddleware']

import logging
from fastapi import __version__

from rollbar.contrib.asgi.integration import integrate
from rollbar.contrib.starlette import LoggerMiddleware as StarletteLoggerMiddleware

log = logging.getLogger(__name__)


@integrate(framework_name=f'fastapi {__version__}')
class LoggerMiddleware(StarletteLoggerMiddleware):
    ...
