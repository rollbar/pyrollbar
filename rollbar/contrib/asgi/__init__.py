import rollbar


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
