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


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, "FastAPI requires Python3.6+")
class FastAPIMiddlewareTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar.contrib.fastapi)

    def test_should_set_fastapi_hook(self):
        self.assertEqual(rollbar.BASE_DATA_HOOK, rollbar.contrib.fastapi._hook)

    def test_should_add_fastapi_version_to_payload(self):
        import fastapi

        with mock.patch("rollbar._check_config", return_value=True):
            with mock.patch("rollbar.send_payload") as mock_send_payload:
                rollbar.report_exc_info()

                mock_send_payload.assert_called_once()
                payload = mock_send_payload.call_args[0][0]

        self.assertIn(fastapi.__version__, payload["data"]["framework"])

    def test_should_catch_and_report_errors(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi import FastAPIMiddleware

        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)

        @app.get("/")
        async def read_root():
            1 / 0

        client = TestClient(app)
        with mock.patch("rollbar.report_exc_info") as mock_report:
            with self.assertRaises(ZeroDivisionError):
                client.get("/")

            mock_report.assert_called_once()

            args, kwargs = mock_report.call_args
            self.assertEqual(kwargs, {})

            exc_info, request = args
            exc_type, exc_value, exc_tb = exc_info

            self.assertEqual(exc_type, ZeroDivisionError)
            self.assertIsInstance(exc_value, ZeroDivisionError)

    def test_should_support_type_hints(self):
        from starlette.types import ASGIApp, Receive, Scope, Send

        self.assertDictEqual(
            rollbar.contrib.fastapi.FastAPIMiddleware.__call__.__annotations__,
            {"scope": Scope, "receive": Receive, "send": Send, "return": None},
        )
