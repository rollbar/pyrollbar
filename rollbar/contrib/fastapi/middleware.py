__all__ = ['ReporterMiddleware']

from rollbar.contrib.starlette import ReporterMiddleware as StarletteReporterMiddleware


class ReporterMiddleware(StarletteReporterMiddleware):
    ...
