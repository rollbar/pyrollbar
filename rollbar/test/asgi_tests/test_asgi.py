import importlib
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import unittest2

import rollbar
import rollbar.contrib.asgi
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 5)


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, "ASGI implementation requires Python3.5+")
class ASGIMiddlewareTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar.contrib.asgi)

    def test_should_set_asgi_hook(self):
        self.assertEqual(rollbar.BASE_DATA_HOOK, rollbar.contrib.asgi._hook)

    def test_should_support_http_only(self):
        from rollbar.contrib.asgi import ASGIApp
        from rollbar.test.async_helper import FailingTestASGIApp

        testapp = FailingTestASGIApp()

        with mock.patch("rollbar.report_exc_info") as mock_report:
            with self.assertRaises(RuntimeError):
                testapp({"type": "http"}, None, None)

            mock_report.assert_called_once()

        with mock.patch("rollbar.report_exc_info") as mock_report:
            with self.assertRaises(RuntimeError):
                testapp({"type": "websocket"}, None, None)

            mock_report.assert_not_called()

    def test_should_support_type_hints_if_starlette_installed(self):
        try:
            from starlette.types import ASGIApp, Receive, Scope, Send
        except ImportError:
            self.skipTest("Support for type hints requires Starlette to be installed")

        self.assertDictEqual(
            rollbar.contrib.asgi.ASGIMiddleware.__call__.__annotations__,
            {"scope": Scope, "receive": Receive, "send": Send, "return": None},
        )
