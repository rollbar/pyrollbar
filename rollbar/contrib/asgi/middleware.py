import logging
import sys

import rollbar
from .integration import IntegrationBase, integrate
from .types import ASGIApp, Receive, Scope, Send
from rollbar.lib._async import RollbarAsyncError, try_report

log = logging.getLogger(__name__)


@integrate(framework_name='asgi')
class ReporterMiddleware(IntegrationBase):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__()

        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await self.app(scope, receive, send)
        except Exception:
            if scope['type'] == 'http':
                exc_info = sys.exc_info()

                try:
                    await try_report(exc_info)
                except RollbarAsyncError:
                    log.warning(
                        'Failed to report asynchronously. Trying to report synchronously.'
                    )
                    rollbar.report_exc_info(exc_info)
            raise
