__all__ = ['LoggerMiddleware']

import logging
import sys

from starlette import __version__
from starlette.types import ASGIApp, Receive, Scope, Send

from rollbar.contrib.asgi import ReporterMiddleware as ASGIReporterMiddleware
from rollbar.contrib.asgi.integration import integrate
from rollbar.contrib.starlette.requests import store_current_request

log = logging.getLogger(__name__)


@integrate(framework_name=f'starlette {__version__}')
class LoggerMiddleware(ASGIReporterMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        if sys.version_info < (3, 6):
            log.error(
                'LoggerMiddleware requires Python 3.7+ (or 3.6 with `aiocontextvars` package)'
            )
            raise RuntimeError(
                'LoggerMiddleware requires Python 3.7+ (or 3.6 with `aiocontextvars` package)'
            )

        super().__init__(app)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        store_current_request(scope, receive)

        await self.app(scope, receive, send)
