import sys

import unittest2

from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 7)


@unittest2.skipUnless(
    ALLOWED_PYTHON_VERSION, 'Global request access requires Python3.7+'
)
class StarletteRequestTest(BaseTest):
    def test_should_accept_request_param(self):
        from starlette.requests import Request
        from rollbar.contrib.starlette.requests import store_current_request
        from rollbar.test.async_helper import async_receive

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

        self.assertEqual(request, stored_request)

    def test_should_accept_scope_and_receive_params(self):
        from starlette.requests import Request
        from rollbar.contrib.starlette.requests import store_current_request
        from rollbar.test.async_helper import async_receive

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

        self.assertEqual(request, expected_request)