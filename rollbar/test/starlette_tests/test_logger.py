import importlib
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import unittest2

import rollbar
import rollbar.contrib.starlette
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 7)


@unittest2.skipUnless(
    ALLOWED_PYTHON_VERSION, 'Starlette LoggerMiddleware requires Python3.7+'
)
class StarletteLoggerTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar.contrib.starlette)

    def test_should_support_type_hints(self):
        from starlette.types import Receive, Scope, Send

        self.assertDictEqual(
            rollbar.contrib.starlette.StarletteMiddleware.__call__.__annotations__,
            {'scope': Scope, 'receive': Receive, 'send': Send, 'return': None},
        )

    @mock.patch('rollbar.contrib.starlette.logger.store_current_request')
    def test_should_store_current_request(self, store_current_request):
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient
        from rollbar.contrib.starlette.logger import LoggerMiddleware

        expected_scope = {
            'client': ['testclient', 50000],
            'headers': [
                (b'host', b'testserver'),
                (b'user-agent', b'testclient'),
                (b'accept-encoding', b'gzip, deflate'),
                (b'accept', b'*/*'),
                (b'connection', b'keep-alive'),
            ],
            'http_version': '1.1',
            'method': 'GET',
            'path': '/',
            'query_string': b'',
            'root_path': '',
            'scheme': 'http',
            'server': ['testserver', 80],
            'type': 'http',
        }

        async def root(request):
            return PlainTextResponse('OK')

        routes = [Route('/{param}', root)]
        middleware = [Middleware(LoggerMiddleware)]
        app = Starlette(routes=routes, middleware=middleware)

        client = TestClient(app)
        client.get('/')

        store_current_request.assert_called_once()

        scope = store_current_request.call_args[0][0]
        self.assertDictContainsSubset(expected_scope, scope)

    def test_should_return_current_request(self):
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient
        from rollbar.contrib.starlette import get_current_request
        from rollbar.contrib.starlette.logger import LoggerMiddleware

        async def root(request):
            self.assertIsNotNone(get_current_request())

            return PlainTextResponse('OK')

        routes = [Route('/', root)]
        middleware = [Middleware(LoggerMiddleware)]
        app = Starlette(routes=routes, middleware=middleware)

        client = TestClient(app)
        client.get('/')

    @mock.patch('rollbar.contrib.starlette.requests.ContextVar', None)
    @mock.patch('logging.Logger.error')
    def test_should_not_return_current_request_for_older_python(self, mock_log):
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient
        from rollbar.contrib.starlette import get_current_request
        from rollbar.contrib.starlette.logger import LoggerMiddleware

        async def root(request):
            self.assertIsNone(get_current_request())
            mock_log.assert_called_once_with(
                'To receive current request Python 3.7+ is required'
            )

            return PlainTextResponse('OK')

        routes = [Route('/', root)]
        middleware = [Middleware(LoggerMiddleware)]
        app = Starlette(routes=routes, middleware=middleware)

        client = TestClient(app)
        client.get('/')
