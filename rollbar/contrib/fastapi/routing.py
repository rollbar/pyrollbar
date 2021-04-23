__all__ = ['add_to']

import logging
import sys
from typing import Callable, Optional, Type, Union

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.routing import APIRoute

import rollbar
from rollbar.contrib.fastapi.utils import fastapi_min_version
from rollbar.contrib.fastapi.utils import get_installed_middlewares
from rollbar.contrib.starlette.requests import store_current_request

log = logging.getLogger(__name__)


@fastapi_min_version('0.41.0')
def add_to(app_or_router: Union[FastAPI, APIRouter]) -> Optional[Type[APIRoute]]:
    # Route handler must be added before adding user routes
    expected_middlewares_in_app = 4
    expected_middlewares_in_router = 0
    if len(app_or_router.routes) not in (
        expected_middlewares_in_app,
        expected_middlewares_in_router,
    ):
        log.error(
            'RollbarLoggingRoute must be added to a bare router'
            ' (before adding routes). See docs for more details.'
        )
        return None

    installed_middlewares = get_installed_middlewares(app_or_router)
    if installed_middlewares:
        log.warn(
            f'Detected installed middlewares {installed_middlewares}'
            ' while loading Rollbar route handler.'
            ' This can cause duplicated occurrences.'
        )

    if isinstance(app_or_router, FastAPI):
        app_or_router.router.route_class = RollbarLoggingRoute
    elif isinstance(app_or_router, APIRouter):
        app_or_router.route_class = RollbarLoggingRoute
    else:
        log.error('Error while adding RollbarLoggingRoute to application')
        return None

    return RollbarLoggingRoute


class RollbarLoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        router_handler = super().get_route_handler()

        async def rollbar_route_handler(request: Request) -> Response:
            try:
                store_current_request(request)
                return await router_handler(request)
            except Exception:
                await request.body()
                exc_info = sys.exc_info()
                rollbar.report_exc_info(exc_info, request)
                raise

        return rollbar_route_handler
