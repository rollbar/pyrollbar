import sys

import rollbar
from .integration import IntegrationBase, integrate
from .types import ASGIApp, Receive, Scope, Send
from rollbar.lib._async import RollbarAsyncError, try_report


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
                    rollbar.report_exc_info(exc_info)
            raise
