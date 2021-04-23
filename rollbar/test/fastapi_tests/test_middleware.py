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

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'FastAPI requires Python3.6+')
class FastAPIMiddlewareTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar.contrib.fastapi)

    @mock.patch('rollbar.report_exc_info')
    def test_should_catch_and_report_errors(self, mock_report):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.middleware import FastAPIMiddleware

        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)

        @app.get('/')
        async def read_root():
            1 / 0

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
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.middleware import FastAPIMiddleware

        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)

        @app.get('/')
        def read_root():
            1 / 0

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
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.middleware import FastAPIMiddleware

        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)

        @app.get('/{path}')
        def read_root(path):
            1 / 0

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
        import rollbar.contrib.fastapi.middleware

        self.assertDictEqual(
            rollbar.contrib.fastapi.middleware.FastAPIMiddleware.__call__.__annotations__,
            {'scope': Scope, 'receive': Receive, 'send': Send, 'return': None},
        )

    @unittest2.skipUnless(
        sys.version_info >= (3, 7), 'Global request access requires Python 3.7+'
    )
    @mock.patch('rollbar.contrib.starlette.middleware.store_current_request')
    def test_should_store_current_request(self, store_current_request):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.middleware import FastAPIMiddleware

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
        app.add_middleware(FastAPIMiddleware)

        @app.get('/')
        async def read_root(request):
            return 'ok'

        client = TestClient(app)
        client.get('/')

        store_current_request.assert_called_once()

        scope = store_current_request.call_args[0][0]
        self.assertDictContainsSubset(expected_scope, scope)

    @unittest2.skipUnless(
        sys.version_info >= (3, 7), 'Global request access is supported in Python 3.7+'
    )
    def test_should_return_current_request(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from starlette.requests import Request
        from rollbar.contrib.fastapi.middleware import FastAPIMiddleware
        from rollbar.contrib.fastapi import get_current_request

        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)

        @app.get('/')
        async def read_root(request):
            request = get_current_request()

            self.assertIsNotNone(request)
            self.assertIsInstance(request, Request)

        client = TestClient(app)
        client.get('/')

    @unittest2.skipIf(
        sys.version_info >= (3, 7), 'Global request access is supported in Python 3.7+'
    )
    def test_should_not_return_current_request_for_older_python(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.middleware import FastAPIMiddleware
        from rollbar.contrib.fastapi import get_current_request

        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)

        @app.get('/')
        async def read_root(request):
            self.assertIsNone(get_current_request())

            return 'ok'

        client = TestClient(app)
        client.get('/')
