from rollbar.test import BaseTest
from rollbar.lib.wrap import unwrap_callable
from rollbar.lib.wrap import wrap_callable
import re
import typing
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


def _call_client(client: httpx.Client, url: str) -> httpx.Request:
    """Send through a client with its network pool mocked."""
    request = httpx.Request("GET", url)
    with patch.object(client._transport, "_pool") as mock_pool:
        mock_pool.handle_request.return_value = _MOCK_POOL_RESPONSE
        client._send_single_request(request=request)
    return request


def _call_transport(transport: httpx.HTTPTransport, url: str) -> httpx.Request:
    request = httpx.Request("GET", url)
    with patch.object(transport, "_pool") as mock_pool:
        mock_pool.handle_request.return_value = _MOCK_POOL_RESPONSE
        transport.handle_request(request)
    return request


async def _call_async_client(client: httpx.AsyncClient, url: str) -> httpx.Request:
    """Send through an async client with its network pool mocked."""
    request = httpx.Request("GET", url)
    transport = typing.cast(httpx.AsyncHTTPTransport, client._transport)
    with patch.object(transport._pool, "handle_async_request") as mock_pool:
        mock_pool.return_value = _MOCK_POOL_RESPONSE
        await client._send_single_request(request=request)
    return request

@unittest.skipUnless(
    HTTPX_INSTALLED,
    'httpx is not installed',
)
class PerClientInstrumentationTest(BaseTest):
    def setUp(self):
        HTTPXContextPropagationManager.uninstrument()
        self.transport = httpx.HTTPTransport()
        self.client = httpx.Client(transport=self.transport)

    def tearDown(self):
        HTTPXContextPropagationManager.uninstrument_client(self.client)
        self.client.close()

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_client_injects_baggage_on_matching_url(self, _mock):
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
        request = _call_client(self.client, "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_client_injects_baggage_with_default_enabled_headers(self, _mock):
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS)
        request = _call_client(self.client, "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_client_does_not_inject_on_non_matching_url(self, _mock):
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
        request = _call_client(self.client, "http://other.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=None)
    def test_per_client_does_not_inject_when_no_session(self, _mock):
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
        request = _call_client(self.client, "http://target.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_client_does_not_affect_uninstrumented_transport(self, _mock):
        other_transport = httpx.HTTPTransport()
        other_client = httpx.Client(transport=other_transport)
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
        request = _call_client(other_client, "http://target.example.com/path")
        other_client.close()
        other_transport.close()
        self.assertIsNone(request.headers.get("baggage"))

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_client_patch_receives_request_not_self_in_args(self, _mock):
        """wrap_callable instance-level: patch_fn must receive (request,) not (transport, request)."""
        received_args = []

        def capturing_patch_fn(wrapped, *args, **kwargs):
            received_args.extend(args)
            return wrapped(*args, **kwargs)

        wrap_callable(self.transport, "handle_request", capturing_patch_fn)
        try:
            _call_transport(self.transport, "http://target.example.com/path")
        finally:
            unwrap_callable(self.transport, "handle_request")

        self.assertEqual(len(received_args), 1)
        self.assertIsInstance(received_args[0], httpx.Request)

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_class_and_instance_patch_receive_identical_args(self, _mock):
        """Class-level and instance-level patches must pass the same args to patch_fn."""
        class_received = []
        instance_received = []

        owner_cls = type("_SubTransport", (httpx.HTTPTransport,), {})
        owner_inst = owner_cls()

        wrap_callable(owner_cls, "handle_request", lambda w, *a, **kw: class_received.append(a) or w(*a, **kw))
        wrap_callable(owner_inst, "handle_request", lambda w, *a, **kw: instance_received.append(a) or w(*a, **kw))
        try:
            _call_transport(owner_inst, "http://target.example.com/path")
        finally:
            unwrap_callable(owner_cls, "handle_request")
            unwrap_callable(owner_inst, "handle_request")
            owner_inst.close()

        self.assertEqual(len(class_received), 1)
        self.assertEqual(len(instance_received), 1)
        self.assertIsInstance(class_received[0][0], httpx.Request)
        self.assertEqual(class_received[0], instance_received[0])


@unittest.skipUnless(
    HTTPX_INSTALLED,
    'httpx is not installed',
)
class PerClientPropagationAsyncTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        HTTPXContextPropagationManager.uninstrument()
        self.transport = httpx.AsyncHTTPTransport()
        self.client = httpx.AsyncClient(transport=self.transport)

    async def asyncTearDown(self):
        HTTPXContextPropagationManager.uninstrument_client(self.client)
        await self.client.aclose()

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=BAGGAGE_VALUE)
    async def test_per_client_injects_baggage_on_matching_url_async_transport(self, _mock):
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
        request = await _call_async_client(self.client, "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.httpx.get_propagation_header", return_value=None)
    async def test_per_client_does_not_inject_when_no_session_async_transport(self, _mock):
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
        request = await _call_async_client(self.client, "http://target.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    def test_per_client_uninstrument_removes_patch(self):
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
        HTTPXContextPropagationManager.uninstrument_client(self.client)
        self.assertFalse(
            getattr(self.client, "_rollbar_httpx_context_propagation_instrumented", False)
        )

    def test_per_client_uninstrument_allows_reinstrumenting_same_client(self):
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
        HTTPXContextPropagationManager.uninstrument_client(self.client)

        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)

        self.assertTrue(getattr(self.client, "_rollbar_httpx_context_propagation_instrumented", False))

    def test_instrument_client_raises_on_double_instrument(self):
        HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
        with self.assertRaises(ValueError):
            HTTPXContextPropagationManager.instrument_client(self.client, ENABLED_URLS, ENABLED_HEADERS)
