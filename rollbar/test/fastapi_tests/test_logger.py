import importlib
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import unittest2

import rollbar
import rollbar.contrib.fastapi
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 7)


@unittest2.skipUnless(
    ALLOWED_PYTHON_VERSION, 'FastAPI LoggerMiddleware requires Python3.7+'
)
class FastAPILoggerTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar.contrib.fastapi)

    def test_should_support_type_hints(self):
        from starlette.types import Receive, Scope, Send
        import rollbar.contrib.fastapi.logger

        self.assertDictEqual(
            rollbar.contrib.fastapi.logger.LoggerMiddleware.__call__.__annotations__,
            {'scope': Scope, 'receive': Receive, 'send': Send, 'return': None},
        )

    @mock.patch('rollbar.contrib.starlette.logger.store_current_request')
    def test_should_store_current_request(self, store_current_request):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.logger import LoggerMiddleware

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

        app = FastAPI()
        app.add_middleware(LoggerMiddleware)

        @app.get('/')
        async def read_root(request):
            return 'ok'

        client = TestClient(app)
        client.get('/')

        store_current_request.assert_called_once()

        scope = store_current_request.call_args[0][0]
        self.assertDictContainsSubset(expected_scope, scope)

    def test_should_return_current_request(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from starlette.requests import Request
        from rollbar.contrib.fastapi.logger import LoggerMiddleware
        from rollbar.contrib.fastapi import get_current_request

        app = FastAPI()
        app.add_middleware(LoggerMiddleware)

        @app.get('/')
        async def read_root(request):
            request = get_current_request()

            self.assertIsNotNone(request)
            self.assertIsInstance(request, Request)

        client = TestClient(app)
        client.get('/')


@unittest2.skipIf(
    ALLOWED_PYTHON_VERSION, 'Global request access is supported in Python 3.7+'
)
class FastAPILoggerUnsupportedTest(BaseTest):
    def test_should_not_return_current_request_for_older_python(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.logger import LoggerMiddleware
        from rollbar.contrib.fastapi import get_current_request

        app = FastAPI()
        app.add_middleware(LoggerMiddleware)

        @app.get('/')
        async def read_root(request):
            self.assertIsNone(get_current_request())

            return 'ok'

        client = TestClient(app)
        client.get('/')
