import functools
import logging
from typing import Union

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


def is_current_version_higher_or_equal(current_version, min_version):
    """
    Compare two version strings and return True if the current version is higher or equal to the minimum version.

    Note: This function only compares the release segment of the version string.
    """
    def parse_version(version):
        """Parse the release segment of a version string into a list of strings."""
        parsed = ['']
        current_segment = 0
        for c in version:
            if c.isdigit():
                parsed[current_segment] += c
            elif c == '.':
                current_segment += 1
                parsed.append('')
            else:
                break
        if parsed[-1] == '':
            parsed.pop()
        return parsed

    current = tuple(map(int, parse_version(current_version)))
    minimum = tuple(map(int, parse_version(min_version)))
    return current >= minimum


class fastapi_min_version:
    def __init__(self, min_version):
        self.min_version = min_version

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not is_current_version_higher_or_equal(
                fastapi.__version__,
                self.min_version,
            ):
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


def has_bare_routing(app_or_router: Union[FastAPI, APIRouter]):
    if not isinstance(app_or_router, (FastAPI, APIRouter)):
        return False

    urls = [
        getattr(app_or_router, 'openapi_url', None),
        getattr(app_or_router, 'docs_url', None),
        getattr(app_or_router, 'redoc_url', None),
        getattr(app_or_router, 'swagger_ui_oauth2_redirect_url', None),
    ]

    for route in app_or_router.routes:
        if route is None or route.path in urls:
            continue
        return False

    return True
