import logging
import sys

from starlette import __version__
from starlette.requests import Request
from starlette.types import Receive, Scope, Send

import rollbar
from .requests import store_current_request
from rollbar.contrib.asgi import ReporterMiddleware as ASGIReporterMiddleware
from rollbar.contrib.asgi.integration import integrate
from rollbar.lib._async import RollbarAsyncError, try_report

log = logging.getLogger(__name__)


@integrate(framework_name=f'starlette {__version__}')
class ReporterMiddleware(ASGIReporterMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            store_current_request(scope, receive)
            await self.app(scope, receive, send)
        except Exception:
            if scope['type'] == 'http':
                request = Request(scope, receive)

                # Consuming the request body in Starlette middleware is problematic.
                # See: https://github.com/encode/starlette/issues/495#issuecomment-494008175
                #
                # Uncomment lines below if you know the risks.
                #
                # Starlette requires the `python-multipart` package to parse the content
                # await request.body()
                # await request.form()

                exc_info = sys.exc_info()

                try:
                    await try_report(exc_info, request)
                except RollbarAsyncError:
                    log.warning(
                        'Failed to report asynchronously. Trying to report synchronously.'
                    )
                    rollbar.report_exc_info(exc_info, request)
            raise
