"""
Tests for fastapi instrumentation
"""

import json
import os
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import rollbar
from rollbar.test import BaseTest

# access token for https://rollbar.com/rollbar/pyrollbar
TOKEN = "92c10f5616944b81a2e6f3c6493a0ec2"

# Fastapi works on python +3.6
ALLOWED_PYTHON_VERSION = sys.version_info[0] == 3 and sys.version_info[1] >= 6


try:
    import fastapi  # noqa: F401

    FASTAPI_INSTALLED = True
except ImportError:
    FASTAPI_INSTALLED = False


def create_app():
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/")
    def index():
        return "Index page"

    @app.get("/cause_error")
    @app.post("/cause_error")
    def cause_error():
        raise Exception("Uh oh")

    return app


def init_rollbar(app):
    import rollbar.contrib.fastapi
    from fastapi import Request, status
    from fastapi.responses import Response

    rollbar.init(
        TOKEN,
        "fastapitest",
        root=os.path.dirname(os.path.realpath(__file__)),
        allow_logging_basic_config=True,
        capture_email=True,
        capture_username=True,
    )

    @app.exception_handler(Exception)
    async def handle_unexpected_exceptions(request: Request, exc: Exception):
        """This won't capture HTTPException."""
        try:
            raise exc
        except Exception:
            rollbar.contrib.fastapi.report_exception(request=request)

        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


if ALLOWED_PYTHON_VERSION and FASTAPI_INSTALLED:

    from fastapi.testclient import TestClient

    class FastapiTest(BaseTest):
        def setUp(self):
            super().setUp()
            self.app = create_app()
            init_rollbar(self.app)
            self.client = TestClient(self.app, raise_server_exceptions=False)

        def test_index(self):
            resp = self.client.get("/")
            self.assertEqual(resp.status_code, 200)

        def assertStringEqual(self, left, right):
            if sys.version_info[0] > 2:
                if hasattr(left, "decode"):
                    left = left.decode("ascii")
                if hasattr(right, "decode"):
                    right = right.decode("ascii")

                return self.assertEqual(left, right)
            else:
                return self.assertEqual(left, right)

        @mock.patch("rollbar.send_payload")
        def test_uncaught(self, send_payload):
            resp = self.client.get(
                "/cause_error?foo=bar",
                headers={"X-Real-Ip": "1.2.3.4", "User-Agent": "Fastapi Test"},
            )
            self.assertEqual(resp.status_code, 500)

            self.assertEqual(send_payload.called, True)
            payload = send_payload.call_args[0][0]
            data = payload["data"]

            self.assertIn("body", data)
            self.assertEqual(data["body"]["trace"]["exception"]["class"], "Exception")
            self.assertStringEqual(
                data["body"]["trace"]["exception"]["message"], "Uh oh"
            )

            self.assertIn("request", data)
            self.assertEqual(
                data["request"]["url"], "http://testserver/cause_error?foo=bar"
            )

            self.assertEqual(data["request"]["user_ip"], "1.2.3.4")
            self.assertEqual(data["request"]["method"], "GET")
            self.assertEqual(data["request"]["headers"]["user-agent"], "Fastapi Test")

        @mock.patch("rollbar.send_payload")
        def test_uncaught_json_request(self, send_payload):
            json_body = {"hello": "world"}
            json_body_str = json.dumps(json_body)
            resp = self.client.post(
                "/cause_error",
                data=json_body_str,
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-For": "5.6.7.8",
                },
            )

            self.assertEqual(resp.status_code, 500)

            self.assertEqual(send_payload.called, True)
            payload = send_payload.call_args[0][0]
            data = payload["data"]

            self.assertIn("body", data)
            self.assertEqual(data["body"]["trace"]["exception"]["class"], "Exception")
            self.assertStringEqual(
                data["body"]["trace"]["exception"]["message"], "Uh oh"
            )

            self.assertIn("request", data)
            self.assertEqual(data["request"]["url"], "http://testserver/cause_error")
            self.assertEqual(data["request"]["user_ip"], "5.6.7.8")
            self.assertEqual(data["request"]["method"], "POST")

        @mock.patch("rollbar.send_payload")
        def test_uncaught_no_username_no_email(self, send_payload):
            rollbar.SETTINGS["capture_email"] = False
            rollbar.SETTINGS["capture_username"] = False

            resp = self.client.get(
                "/cause_error?foo=bar",
                headers={"X-Real-Ip": "1.2.3.4", "User-Agent": "Fastapi Test"},
            )
            self.assertEqual(resp.status_code, 500)

            self.assertEqual(send_payload.called, True)
            payload = send_payload.call_args[0][0]
            data = payload["data"]

            self.assertIn("body", data)
            self.assertEqual(data["body"]["trace"]["exception"]["class"], "Exception")
            self.assertStringEqual(
                data["body"]["trace"]["exception"]["message"], "Uh oh"
            )

            self.assertIn("request", data)
            self.assertEqual(
                data["request"]["url"], "http://testserver/cause_error?foo=bar"
            )

            self.assertEqual(data["request"]["user_ip"], "1.2.3.4")
            self.assertEqual(data["request"]["method"], "GET")
            self.assertEqual(data["request"]["headers"]["user-agent"], "Fastapi Test")

            rollbar.SETTINGS["capture_email"] = True
            rollbar.SETTINGS["capture_username"] = True
