import sys

try:
    import fastapi

    FASTAPI_INSTALLED = True
except ImportError:
    FASTAPI_INSTALLED = False

import unittest

from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest.skipUnless(
    FASTAPI_INSTALLED and ALLOWED_PYTHON_VERSION, 'FastAPI requires Python3.6+'
)
class UtilsMiddlewareTest(BaseTest):
    def test_should_return_installed_rollbar_middlewares(self):
        from fastapi import FastAPI
        from rollbar.contrib.fastapi.utils import get_installed_middlewares
        from rollbar.contrib.fastapi import ReporterMiddleware as FastAPIMiddleware
        from rollbar.contrib.starlette import ReporterMiddleware as StarletteMiddleware
        from rollbar.contrib.asgi import ReporterMiddleware as ASGIMiddleware

        # single middleware
        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)

        middlewares = get_installed_middlewares(app)

        self.assertListEqual(middlewares, [FastAPIMiddleware])

        # multiple middlewares
        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)
        app.add_middleware(StarletteMiddleware)
        app.add_middleware(ASGIMiddleware)

        middlewares = get_installed_middlewares(app)

        self.assertListEqual(
            middlewares, ([ASGIMiddleware, StarletteMiddleware, FastAPIMiddleware])
        )

    def test_should_return_empty_list_if_rollbar_middlewares_not_installed(self):
        from fastapi import FastAPI
        from rollbar.contrib.fastapi.utils import get_installed_middlewares
        from rollbar.lib._async import BareMiddleware

        # no middlewares
        app = FastAPI()

        middlewares = get_installed_middlewares(app)

        self.assertListEqual(middlewares, [])

        # no Rollbar middlewares
        app = FastAPI()
        app.add_middleware(BareMiddleware)

        middlewares = get_installed_middlewares(app)

        self.assertListEqual(middlewares, [])


@unittest.skipUnless(
    FASTAPI_INSTALLED and ALLOWED_PYTHON_VERSION, 'FastAPI requires Python3.6+'
)
class UtilsBareRoutingTest(BaseTest):
    def test_should_return_true_if_has_bare_routing(self):
        from fastapi import APIRouter, FastAPI
        from rollbar.contrib.fastapi.utils import has_bare_routing

        app = FastAPI()
        self.assertTrue(has_bare_routing(app))

        router = APIRouter()
        self.assertTrue(has_bare_routing(router))

    def test_should_return_false_if_user_routes_added_to_app(self):
        from fastapi import APIRouter, FastAPI
        from rollbar.contrib.fastapi.utils import has_bare_routing

        app = FastAPI()
        self.assertTrue(has_bare_routing(app))

        @app.get('/')
        async def read_root():
            ...

        self.assertFalse(has_bare_routing(app))

    def test_should_return_false_if_user_routes_added_to_router(self):
        from fastapi import APIRouter
        from rollbar.contrib.fastapi.utils import has_bare_routing

        router = APIRouter()
        self.assertTrue(has_bare_routing(router))

        @router.get('/')
        async def read_root():
            ...

        self.assertFalse(has_bare_routing(router))

    def test_should_return_false_if_router_added_to_app(self):
        from fastapi import APIRouter, FastAPI
        from rollbar.contrib.fastapi.utils import has_bare_routing

        app = FastAPI()
        router = APIRouter()
        self.assertTrue(has_bare_routing(app))

        @router.get('/')
        async def read_root():
            ...

        app.include_router(router)

        self.assertFalse(has_bare_routing(app))

    def test_should_return_true_if_docs_disabled(self):
        from fastapi import APIRouter, FastAPI
        from rollbar.contrib.fastapi.utils import has_bare_routing

        app = FastAPI(docs_url=None, redoc_url=None)
        self.assertTrue(has_bare_routing(app))

        app = FastAPI(docs_url=None)
        self.assertTrue(has_bare_routing(app))

        app = FastAPI(redoc_url=None)
        self.assertTrue(has_bare_routing(app))

        router = APIRouter()
        self.assertTrue(has_bare_routing(router))

@unittest.skipUnless(
    FASTAPI_INSTALLED and ALLOWED_PYTHON_VERSION, 'FastAPI requires Python3.6+'
)
class UtilsVersionCompareTest(BaseTest):
    def test_is_current_version_higher_or_equal(self):
        # Copied from https://semver.org/#spec-item-11
        versions = [
            '1.0.0-alpha',
            '1.0.0-alpha.1',
            '1.0.0-alpha.beta',
            '1.0.0-beta',
            '1.0.0-beta.2',
            '1.0.0-beta.11',
            '1.0.0-rc.1',
            '1.0.0',
            '1.1.1',
            '1.100.0-beta2',
            '1.100.0-beta3',
        ]

        from rollbar.contrib.fastapi.utils import is_current_version_higher_or_equal

        previous_version = None
        for version in versions:
            print(f'{version} >= {previous_version}')
            if previous_version is None:
                previous_version = version
                continue
            with self.subTest(f'{version} >= {previous_version}'):
                self.assertTrue(is_current_version_higher_or_equal(version, previous_version))
            previous_version = version
