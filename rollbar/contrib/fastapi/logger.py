__all__ = ['LoggerMiddleware']

from fastapi import __version__

from rollbar.contrib.asgi.integration import integrate
from rollbar.contrib.starlette import LoggerMiddleware as StarletteLoggerMiddleware


@integrate(framework_name=f'fastapi {__version__}')
class LoggerMiddleware(StarletteLoggerMiddleware):
    ...
