__all__ = ['FastAPIMiddleware', 'add_to']

import sys
from typing import Callable, Type

from fastapi import Request, Response, __version__
from fastapi.routing import APIRoute
from starlette.types import ASGIApp

import rollbar
from rollbar.contrib.fastapi.utils import fastapi_min_version
from rollbar.contrib.starlette import StarletteMiddleware


class FastAPIMiddleware(StarletteMiddleware):
    ...


@fastapi_min_version('0.41.0')
def add_to(app: ASGIApp) -> Type[APIRoute]:
    class RollbarLoggingRoute(app.router.route_class):
        def get_route_handler(self) -> Callable:
            original_router_handler = super().get_route_handler()

            async def custom_route_handler(request: Request) -> Response:
                try:
                    return await original_router_handler(request)
                except Exception:
                    await request.body()
                    exc_info = sys.exc_info()
                    rollbar.report_exc_info(exc_info, request)
                    raise

            return custom_route_handler

    app.router.route_class = RollbarLoggingRoute


def _hook(request, data):
    data['framework'] = f'fastapi {__version__}'


rollbar.BASE_DATA_HOOK = _hook
