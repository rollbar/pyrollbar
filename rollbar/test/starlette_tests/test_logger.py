import importlib
import sys

try:
    from unittest import mock
except ImportError:
    import mock

try:
    import starlette

    STARLETTE_INSTALLED = True
except ImportError:
    STARLETTE_INSTALLED = False

import unittest2

import rollbar
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest2.skipUnless(
    STARLETTE_INSTALLED and ALLOWED_PYTHON_VERSION,
    'Starlette LoggerMiddleware requires Python3.6+',
)
class LoggerMiddlewareTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar)

    @mock.patch('rollbar._check_config', return_value=True)
    @mock.patch('rollbar.send_payload')
    def test_should_add_framework_version_to_payload(self, mock_send_payload, *mocks):
        import starlette
        from starlette.applications import Starlette
        import rollbar
        from rollbar.contrib.starlette.logger import LoggerMiddleware

        self.assertIsNone(rollbar.BASE_DATA_HOOK)

        app = Starlette()
        app.add_middleware(LoggerMiddleware)

        rollbar.report_exc_info()

        mock_send_payload.assert_called_once()
        payload = mock_send_payload.call_args[0][0]

        self.assertIn('starlette', payload['data']['framework'])
        self.assertIn(starlette.__version__, payload['data']['framework'])

    def test_should_support_type_hints(self):
        from starlette.types import Receive, Scope, Send
        import rollbar.contrib.starlette.logger

        self.assertDictEqual(
            rollbar.contrib.starlette.logger.LoggerMiddleware.__call__.__annotations__,
            {'scope': Scope, 'receive': Receive, 'send': Send, 'return': None},
        )

    @mock.patch('rollbar.contrib.starlette.logger.store_current_request')
    def test_should_store_current_request(self, store_current_request):
        from starlette.applications import Starlette
        from starlette.responses import PlainTextResponse
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

        app = Starlette()
        app.add_middleware(LoggerMiddleware)

        @app.route('/{param}')
        async def root(request):
            return PlainTextResponse('OK')

        client = TestClient(app)
        client.get('/')

        store_current_request.assert_called_once()

        scope = store_current_request.call_args[0][0]
        self.assertDictContainsSubset(expected_scope, scope)

    def test_should_return_current_request(self):
        from starlette.applications import Starlette
        from starlette.responses import PlainTextResponse
        from starlette.testclient import TestClient
        from rollbar.contrib.starlette import get_current_request
        from rollbar.contrib.starlette.logger import LoggerMiddleware

        app = Starlette()
        app.add_middleware(LoggerMiddleware)

        @app.route('/')
        async def root(request):
            self.assertIsNotNone(get_current_request())

            return PlainTextResponse('OK')

        client = TestClient(app)
        client.get('/')

    @mock.patch('rollbar.contrib.starlette.requests.ContextVar', None)
    @mock.patch('logging.Logger.error')
    def test_should_not_return_current_request_for_older_python(self, mock_log):
        from starlette.applications import Starlette
        from starlette.responses import PlainTextResponse
        from starlette.testclient import TestClient
        from rollbar.contrib.starlette import get_current_request
        from rollbar.contrib.starlette.logger import LoggerMiddleware

        app = Starlette()
        app.add_middleware(LoggerMiddleware)

        @app.route('/')
        async def root(request):
            self.assertIsNone(get_current_request())
            mock_log.assert_called_once_with(
                'Python 3.7+ (or aiocontextvars package) is required to receive current request.'
            )

            return PlainTextResponse('OK')

        client = TestClient(app)
        client.get('/')
