import sys

try:
    import starlette

    STARLETTE_INSTALLED = True
except ImportError:
    STARLETTE_INSTALLED = False

import unittest

from rollbar.test import BaseTest
from rollbar.test.utils import get_public_attrs

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest.skipUnless(
    STARLETTE_INSTALLED and ALLOWED_PYTHON_VERSION,
    'Global request access requires Python3.6+',
)
class RequestTest(BaseTest):
    def test_should_accept_request_param(self):
        from starlette.requests import Request
        from rollbar.contrib.starlette.requests import store_current_request
        from rollbar.lib._async import async_receive

        scope = {
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
        receive = async_receive(
            {'type': 'http.request', 'body': b'body body', 'mode_body': False}
        )
        request = Request(scope, receive)

        stored_request = store_current_request(request)

        self.assertEqual(get_public_attrs(request), get_public_attrs(stored_request))

    def test_should_accept_scope_param_if_http_type(self):
        from starlette.requests import Request
        from rollbar.contrib.starlette.requests import store_current_request
        from rollbar.lib._async import async_receive

        scope = {
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
        receive = async_receive(
            {'type': 'http.request', 'body': b'body body', 'mode_body': False}
        )
        expected_request = Request(scope, receive)

        request = store_current_request(scope, receive)

        self.assertEqual(get_public_attrs(request), get_public_attrs(expected_request))

    def test_should_not_accept_scope_param_if_not_http_type(self):
        from rollbar.contrib.starlette.requests import store_current_request

        scope = {'asgi': {'spec_version': '2.0', 'version': '3.0'}, 'type': 'lifespan'}
        receive = {}

        request = store_current_request(scope, receive)

        self.assertIsNone(request)

    def test_hasuser(self):
        from starlette.requests import Request
        from rollbar.contrib.starlette.requests import hasuser

        request = Request({'type': 'http'}, {})
        self.assertFalse(hasuser(request))

        request = Request({'type': 'http', 'user': 'testuser'}, {})
        self.assertTrue(hasuser(request))
        self.assertEqual(request.user, 'testuser')
