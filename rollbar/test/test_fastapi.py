import sys

try:
    from unittest import mock
except ImportError:
    import mock

import unittest2

from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info[0] >= 3 and sys.version_info[1] >= 6


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, "FastAPI requires Python3.6+")
class FastAPIMiddlewareTest(BaseTest):
    def test_should_set_fastapi_hook(self):
        import rollbar
        import rollbar.contrib.fastapi

        self.assertEqual(rollbar.BASE_DATA_HOOK, rollbar.contrib.fastapi._hook)

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

            self.assertEqual(mock_report.call_count, 1)

            args, kwargs = mock_report.call_args
            self.assertEqual(kwargs, {})

            exc_info, request = args

            exc_type, exc_value, exc_tb = exc_info
            self.assertEqual(exc_type, ZeroDivisionError)
            self.assertIsInstance(exc_value, ZeroDivisionError)
