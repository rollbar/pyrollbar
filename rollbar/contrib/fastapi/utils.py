import functools
import logging

import fastapi
from fastapi import APIRouter, FastAPI

from . import ReporterMiddleware as FastAPIReporterMiddleware
from rollbar.contrib.starlette import ReporterMiddleware as StarletteReporterMiddleware
from rollbar.contrib.asgi import ReporterMiddleware as ASGIReporterMiddleware

log = logging.getLogger(__name__)


class FastAPIVersionError(Exception):
    def __init__(self, version, reason=''):
        err_msg = f'FastAPI {version}+ is required'
        if reason:
            err_msg += f' {reason}'

        log.error(err_msg)
        return super().__init__(err_msg)


class fastapi_min_version:
    def __init__(self, min_version):
        self.min_version = min_version

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if fastapi.__version__ < self.min_version:
                raise FastAPIVersionError(
                    self.min_version, reason=f'to use {func.__name__}() function'
                )

            return func(*args, **kwargs)

        return wrapper


def get_installed_middlewares(app):
    candidates = (
        FastAPIReporterMiddleware,
        StarletteReporterMiddleware,
        ASGIReporterMiddleware,
    )

    middlewares = []

    if hasattr(app, 'user_middleware'):  # FastAPI v0.51.0+
        middlewares = [
            middleware.cls
            for middleware in app.user_middleware
            if middleware.cls in candidates
        ]
    elif hasattr(app, 'error_middleware'):
        middleware = app.error_middleware

        while hasattr(middleware, 'app'):
            if isinstance(middleware, candidates):
                middlewares.append(middleware)
            middleware = middleware.app

        middlewares = [middleware.__class__ for middleware in middlewares]

    return middlewares


def has_bare_routing(app_or_router):
    expected_app_routes = 4
    expected_router_routes = 0

    if (
        isinstance(app_or_router, FastAPI)
        and expected_app_routes != len(app_or_router.routes)
    ) or (
        isinstance(app_or_router, APIRouter)
        and expected_router_routes != len(app_or_router.routes)
    ):
        return False

    return True
