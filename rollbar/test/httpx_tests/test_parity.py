from __future__ import annotations

import gc
import re
import weakref
from functools import wraps
from unittest.mock import patch

import httpx

from rollbar.contrib.httpx import HTTPXContextPropagationManager
from rollbar.test import BaseTest


ALLOWED = [re.compile(r"^http://target\.example\.com.*")]
BAGGAGE = "rollbar.session.id=abc, rollbar.execution.scope.id=123"


class TestHTTPXPropagationParity(BaseTest):
    def setUp(self):
        HTTPXContextPropagationManager.uninstrument()

    def tearDown(self):
        HTTPXContextPropagationManager.uninstrument()

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE)
    def test_global_supports_custom_transport_and_replaces_rollbar_baggage(self, _mock):
        seen = []

        def handler(request):
            seen.append(request.headers.get("baggage"))
            return httpx.Response(200)

        HTTPXContextPropagationManager.instrument(ALLOWED, ["baggage"])
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            client.get(
                "http://target.example.com/path",
                headers={"baggage": "vendor.key=value, rollbar.session.id=stale"},
            )

        self.assertEqual(seen, [f"vendor.key=value, {BAGGAGE}"])

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE)
    def test_redirect_does_not_leak_rollbar_baggage(self, _mock):
        seen = []

        def handler(request):
            seen.append(request.headers.get("baggage"))
            if len(seen) == 1:
                return httpx.Response(
                    302, headers={"location": "http://outside.example.com/landing"}
                )
            return httpx.Response(200)

        HTTPXContextPropagationManager.instrument(ALLOWED, ["baggage"])
        with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
            client.get("http://target.example.com/path")

        self.assertEqual(seen, [BAGGAGE, None])

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE)
    def test_per_client_overrides_global_without_duplicate_baggage(self, _mock):
        seen = []
        transport = httpx.MockTransport(
            lambda request: seen.append(request.headers.get("baggage")) or httpx.Response(200)
        )
        HTTPXContextPropagationManager.instrument(ALLOWED, ["baggage"])
        with httpx.Client(transport=transport) as client:
            HTTPXContextPropagationManager.instrument_client(client, ALLOWED, ["baggage"])
            client.get("http://target.example.com/path")
            HTTPXContextPropagationManager.uninstrument_client(client)
            client.get("http://target.example.com/path")

        self.assertEqual(seen, [BAGGAGE, BAGGAGE])

    def test_client_with_none_mount_can_be_instrumented_and_uninstrumented(self):
        with httpx.Client(mounts={"all://example.com": None}) as client:
            HTTPXContextPropagationManager.instrument_client(client, ALLOWED)
            HTTPXContextPropagationManager.uninstrument_client(client)

    def test_instrumentation_does_not_keep_client_alive(self):
        client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200)))
        HTTPXContextPropagationManager.instrument_client(client, ALLOWED)
        reference = weakref.ref(client)
        del client
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(len(HTTPXContextPropagationManager._clients), 0)

    def test_global_uninstrument_preserves_later_wrapper(self):
        original = httpx.Client._send_single_request
        HTTPXContextPropagationManager.instrument(ALLOWED, ["baggage"])

        @wraps(httpx.Client._send_single_request)
        def other_wrapper(client, request):
            return other_wrapper.__wrapped__(client, request)

        httpx.Client._send_single_request = other_wrapper
        try:
            HTTPXContextPropagationManager.uninstrument()
            self.assertIs(httpx.Client._send_single_request, other_wrapper)
        finally:
            httpx.Client._send_single_request = original
