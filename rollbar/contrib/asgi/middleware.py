import rollbar
from rollbar.contrib.asgi.types import ASGIApp, Receive, Scope, Send


class ASGIMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await self.app(scope, receive, send)
        except Exception:
            if scope['type'] == 'http':
                rollbar.report_exc_info()
            raise
