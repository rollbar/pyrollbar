import importlib
import sys

from unittest import mock

try:
    import fastapi

    FASTAPI_INSTALLED = True
except ImportError:
    FASTAPI_INSTALLED = False

import unittest

import rollbar
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest.skipUnless(
    FASTAPI_INSTALLED and ALLOWED_PYTHON_VERSION,
    'FastAPI LoggerMiddleware requires Python3.6+',
)
class LoggerMiddlewareTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar)

    @mock.patch('rollbar._check_config', return_value=True)
    @mock.patch('rollbar.send_payload')
    def test_should_add_framework_version_to_payload(self, mock_send_payload, *mocks):
        import fastapi
        from fastapi import FastAPI
        import rollbar
        from rollbar.contrib.fastapi.logger import LoggerMiddleware

        self.assertIsNone(rollbar.BASE_DATA_HOOK)

        app = FastAPI()
        app.add_middleware(LoggerMiddleware)
        app.build_middleware_stack()

        rollbar.report_exc_info()

        mock_send_payload.assert_called_once()
        payload = mock_send_payload.call_args[0][0]

        self.assertIn('fastapi', payload['data']['framework'])
        self.assertIn(fastapi.__version__, payload['data']['framework'])

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
        from rollbar.contrib.fastapi.logger import LoggerMiddleware

        try:
            from fastapi.testclient import TestClient
        except ImportError:  # Added in FastAPI v0.51.0+
            from starlette.testclient import TestClient

        expected_scope = {
            'client': ['testclient', 50000],
            'headers': [
                (b'host', b'testserver'),
                (b'accept', b'*/*'),
                (b'accept-encoding', b'gzip, deflate'),
                (b'connection', b'keep-alive'),
                (b'user-agent', b'testclient'),
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
        async def read_root():
            return 'ok'

        client = TestClient(app)
        client.get('/')

        store_current_request.assert_called_once()

        scope = store_current_request.call_args[0][0]
        self.assertEqual(scope, {**expected_scope, **scope})

    def test_should_return_current_request(self):
        from fastapi import FastAPI
        from starlette.requests import Request
        from rollbar.contrib.fastapi.logger import LoggerMiddleware
        from rollbar.contrib.fastapi import get_current_request

        try:
            from fastapi.testclient import TestClient
        except ImportError:  # Added in FastAPI v0.51.0+
            from starlette.testclient import TestClient

        app = FastAPI()
        app.add_middleware(LoggerMiddleware)

        @app.get('/')
        async def read_root():
            request = get_current_request()

            self.assertIsNotNone(request)
            self.assertIsInstance(request, Request)

        client = TestClient(app)
        client.get('/')

    @mock.patch('rollbar.contrib.starlette.requests.ContextVar', None)
    @mock.patch('logging.Logger.error')
    def test_should_not_return_current_request_for_older_python(self, mock_log):
        from fastapi import FastAPI
        from rollbar.contrib.fastapi.logger import LoggerMiddleware
        from rollbar.contrib.fastapi import get_current_request

        try:
            from fastapi.testclient import TestClient
        except ImportError:  # Added in FastAPI v0.51.0+
            from starlette.testclient import TestClient

        app = FastAPI()
        app.add_middleware(LoggerMiddleware)

        @app.get('/')
        async def read_root():
            self.assertIsNone(get_current_request())
            mock_log.assert_called_once_with(
                'Python 3.7+ (or aiocontextvars package)'
                ' is required to receive current request.'
            )

        client = TestClient(app)
        client.get('/')
