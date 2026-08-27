from rollbar.lib.wrap import wrap_callable, unwrap_callable
from rollbar.test import BaseTest
import re
import unittest
import httpcore

from unittest.mock import patch

from rollbar.contrib.httpx import HTTPXContextPropagationManager

try:
    import httpx

    HTTPX_INSTALLED = True
except ImportError:
    HTTPX_INSTALLED = False

ENABLED_URLS = [re.compile(r"^http://target\.example\.com.*")]
ENABLED_HEADERS = ["baggage"]
BAGGAGE_VALUE = "rollbar.session.id=abc; rollbar.execution.scope.id=123"
_MOCK_POOL_RESPONSE = httpcore.Response(200, content=b"")


def _call_transport(transport: httpx.HTTPTransport, url: str) -> httpx.Request:
    """Send through a client with its network pool mocked."""
    request = httpx.Request("GET", url)
    client = httpx.Client(transport=transport)
    try:
        with patch.object(transport, "_pool") as mock_pool:
            mock_pool.handle_request.return_value = _MOCK_POOL_RESPONSE
            client._send_single_request(request=request)
            mock_pool.handle_request.assert_called_once()
    finally:
        client.close()
    return request


async def _call_async_transport(transport: httpx.AsyncHTTPTransport, url: str) -> httpx.Request:
    """Send through an async client with its network pool mocked."""
    request = httpx.Request("GET", url)
    client = httpx.AsyncClient(transport=transport)
    try:
        with patch.object(transport._pool, "handle_async_request") as mock_pool:
            mock_pool.return_value = _MOCK_POOL_RESPONSE
            await client._send_single_request(request=request)
            mock_pool.assert_awaited_once()
    finally:
        await client.aclose()
    return request

@unittest.skipUnless(
    HTTPX_INSTALLED,
    'httpx is not installed',
)
class TestGlobalPropagation(BaseTest):
    def setUp(self):
        HTTPXContextPropagationManager.uninstrument()

    def tearDown(self):
        HTTPXContextPropagationManager.uninstrument()

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_injects_baggage_on_matching_url(self, _mock):
        HTTPXContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = _call_transport(httpx.HTTPTransport(), "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_injects_baggage_on_exact_url_match(self, _mock):
        HTTPXContextPropagationManager.instrument(["http://target.example.com/path"], ENABLED_HEADERS)
        request = _call_transport(httpx.HTTPTransport(), "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_normalizes_exact_root_url(self, _mock):
        HTTPXContextPropagationManager.instrument(["http://target.example.com/"], ENABLED_HEADERS)
        request = _call_transport(httpx.HTTPTransport(), "http://target.example.com")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_does_not_inject_on_non_matching_url(self, _mock):
        HTTPXContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = _call_transport(httpx.HTTPTransport(), "http://other.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=None)
    def test_global_does_not_inject_when_no_session(self, _mock):
        HTTPXContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = _call_transport(httpx.HTTPTransport(), "http://target.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch(
        "rollbar.contrib.httpx.get_propagation_header",
        side_effect=RuntimeError("propagation failed"),
    )
    def test_global_sends_request_when_injection_fails(self, _mock):
        HTTPXContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)

        with self.assertLogs("rollbar.contrib.httpx", level="ERROR") as logs:
            request = _call_transport(httpx.HTTPTransport(), "http://target.example.com/path")

        self.assertIsNone(request.headers.get("baggage"))
        self.assertEqual(
            logs.output,
            [
                "ERROR:rollbar.contrib.httpx:Error injecting Rollbar "
                "propagation headers into request: propagation failed"
            ],
        )

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_honors_enabled_headers(self, _mock):
        HTTPXContextPropagationManager.instrument(["http://target.example.com/path"], ["traceparent"])
        request = _call_transport(httpx.HTTPTransport(), "http://target.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))
        self.assertIsNone(request.headers.get("traceparent"))

    def test_global_uninstrument_removes_patch(self):
        HTTPXContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        HTTPXContextPropagationManager.uninstrument()
        self.assertFalse(HTTPXContextPropagationManager._globally_instrumented)

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_patch_receives_request_not_self_in_args(self, _mock):
        """wrap_callable class-level: patch_fn must receive (request,) not (transport, request)."""
        received_args = []

        def capturing_patch_fn(wrapped, *args, **kwargs):
            received_args.extend(args)
            return wrapped(*args, **kwargs)

        wrap_callable(httpx.HTTPTransport, "handle_request", capturing_patch_fn)
        try:
            _call_transport(httpx.HTTPTransport(), "http://target.example.com/path")
        finally:
            unwrap_callable(httpx.HTTPTransport, "handle_request")

        self.assertEqual(len(received_args), 1)
        self.assertIsInstance(received_args[0], httpx.Request)


@unittest.skipUnless(
    HTTPX_INSTALLED,
    'httpx is not installed',
)
class TestGlobalPropagationAsync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        HTTPXContextPropagationManager.uninstrument()

    async def asyncTearDown(self):
        HTTPXContextPropagationManager.uninstrument()

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    async def test_global_injects_baggage_on_matching_url_async_transport(self, _mock):
        HTTPXContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = await _call_async_transport(httpx.AsyncHTTPTransport(), "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=None)
    async def test_global_does_not_inject_when_no_session_async_transport(self, _mock):
        HTTPXContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = await _call_async_transport(httpx.AsyncHTTPTransport(), "http://target.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch(
        "rollbar.contrib.httpx.get_propagation_header",
        side_effect=RuntimeError("propagation failed"),
    )
    async def test_global_sends_request_when_injection_fails_async_transport(self, _mock):
        HTTPXContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)

        with self.assertLogs("rollbar.contrib.httpx", level="ERROR") as logs:
            request = await _call_async_transport(
                httpx.AsyncHTTPTransport(),
                "http://target.example.com/path",
            )

        self.assertIsNone(request.headers.get("baggage"))
        self.assertEqual(
            logs.output,
            [
                "ERROR:rollbar.contrib.httpx:Error injecting Rollbar "
                "propagation headers into request: propagation failed"
            ],
        )
