__all__ = ['ReporterMiddleware']

from fastapi import __version__

from rollbar.contrib.asgi.integration import integrate
from rollbar.contrib.starlette import ReporterMiddleware as StarletteReporterMiddleware


@integrate(framework_name=f'fastapi {__version__}')
class ReporterMiddleware(StarletteReporterMiddleware):
    ...
