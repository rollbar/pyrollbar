import rollbar

try:
    from starlette.types import ASGIApp, Receive, Scope, Send
except ImportError:
    STARLETTE_INSTALLED = False
else:
    STARLETTE_INSTALLED = True


if STARLETTE_INSTALLED is True:

    class ASGIMiddleware:
        def __init__(self, app: ASGIApp) -> None:
            self.app = app

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            try:
                await self.app(scope, receive, send)
            except Exception:
                rollbar.report_exc_info()
                raise


else:

    class ASGIMiddleware:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            try:
                await self.app(scope, receive, send)
            except Exception:
                rollbar.report_exc_info()
                raise


def _hook(request, data):
    data["framework"] = "asgi"


rollbar.BASE_DATA_HOOK = _hook
