__all__ = ['StarletteMiddleware']

import sys

from starlette import __version__
from starlette.requests import Request
from starlette.types import Receive, Scope, Send

import rollbar
from rollbar.contrib.asgi import ASGIMiddleware


class StarletteMiddleware(ASGIMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await self.app(scope, receive, send)
        except Exception:
            if scope['type'] == 'http':
                request = Request(scope, receive, send)

                # Consuming the request body in Starlette middleware is problematic
                # See: https://github.com/encode/starlette/issues/495#issuecomment-494008175
                # Uncomment line below if you know the risk
                # await request.body()

                exc_info = sys.exc_info()
                rollbar.report_exc_info(exc_info, request)
            raise


def _hook(request, data):
    data['framework'] = f'starlette {__version__}'


rollbar.BASE_DATA_HOOK = _hook
