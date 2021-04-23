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

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'Starlette requires Python3.6+')
class StarletteMiddlewareTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar.contrib.starlette)

    def test_should_set_starlette_hook(self):
        self.assertEqual(rollbar.BASE_DATA_HOOK, rollbar.contrib.starlette._hook)

    @mock.patch('rollbar._check_config', return_value=True)
    @mock.patch('rollbar.send_payload')
    def test_should_add_starlette_version_to_payload(self, mock_send_payload, *mocks):
        import starlette

        rollbar.report_exc_info()

        mock_send_payload.assert_called_once()
        payload = mock_send_payload.call_args[0][0]

        self.assertIn(starlette.__version__, payload['data']['framework'])

    @mock.patch('rollbar.report_exc_info')
    def test_should_catch_and_report_errors(self, mock_report):
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.routing import Route
        from starlette.testclient import TestClient
        from rollbar.contrib.starlette import StarletteMiddleware

        async def root(request):
            1 / 0

        routes = [Route('/', root)]
        middleware = [Middleware(StarletteMiddleware)]
        app = Starlette(routes=routes, middleware=middleware)

        client = TestClient(app)
        with self.assertRaises(ZeroDivisionError):
            client.get('/')

        mock_report.assert_called_once()

        args, kwargs = mock_report.call_args
        self.assertEqual(kwargs, {})

        exc_type, exc_value, exc_tb = args[0]

        self.assertEqual(exc_type, ZeroDivisionError)
        self.assertIsInstance(exc_value, ZeroDivisionError)

    @mock.patch('rollbar.report_exc_info')
    def test_should_report_with_request_data(self, mock_report):
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.requests import Request
        from starlette.routing import Route
        from starlette.testclient import TestClient
        from rollbar.contrib.starlette import StarletteMiddleware

        async def root(request):
            1 / 0

        routes = [Route('/', root)]
        middleware = [Middleware(StarletteMiddleware)]
        app = Starlette(routes=routes, middleware=middleware)

        client = TestClient(app)
        with self.assertRaises(ZeroDivisionError):
            client.get('/')

        mock_report.assert_called_once()
        request = mock_report.call_args[0][1]

        self.assertIsInstance(request, Request)

    @mock.patch('rollbar._check_config', return_value=True)
    @mock.patch('rollbar._serialize_frame_data')
    @mock.patch('rollbar.send_payload')
    def test_should_send_payload_with_request_data(self, mock_send_payload, *mocks):
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.requests import Request
        from starlette.routing import Route
        from starlette.testclient import TestClient
        from rollbar.contrib.starlette import StarletteMiddleware

        async def root(request):
            1 / 0

        routes = [Route('/{path}', root)]
        middleware = [Middleware(StarletteMiddleware)]
        app = Starlette(routes=routes, middleware=middleware)

        client = TestClient(app)
        with self.assertRaises(ZeroDivisionError):
            client.get('/test?param1=value1&param2=value2')

        mock_send_payload.assert_called_once()
        payload = mock_send_payload.call_args[0][0]
        payload_request = payload['data']['request']

        self.assertEqual(payload_request['method'], 'GET')
        self.assertEqual(payload_request['user_ip'], 'testclient')
        self.assertEqual(
            payload_request['url'],
            'http://testserver/test?param1=value1&param2=value2',
        )
        self.assertDictEqual(payload_request['params'], {'path': 'test'})
        self.assertDictEqual(
            payload_request['GET'], {'param1': 'value1', 'param2': 'value2'}
        )
        self.assertDictEqual(
            payload_request['headers'],
            {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate',
                'connection': 'keep-alive',
                'host': 'testserver',
                'user-agent': 'testclient',
            },
        )

    def test_should_support_type_hints(self):
        from starlette.types import Receive, Scope, Send

        self.assertDictEqual(
            rollbar.contrib.starlette.StarletteMiddleware.__call__.__annotations__,
            {'scope': Scope, 'receive': Receive, 'send': Send, 'return': None},
        )
