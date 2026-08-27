import gc
import re
import requests
import weakref

from unittest.mock import Mock, patch

from rollbar.contrib.requests import RequestsContextPropagationManager
from rollbar.test import BaseTest


ENABLED_URLS = [re.compile(r"^http://target\.example\.com.*")]
ENABLED_HEADERS = ["baggage"]
BAGGAGE_VALUE = "rollbar.session.id=abc, rollbar.execution.scope.id=123"


def _build_response(request: requests.PreparedRequest) -> requests.Response:
    response = requests.Response()
    response.status_code = 200
    response.request = request
    response.url = request.url or ""
    response.raw = None
    return response


def _call_session(session: requests.Session, url: str) -> requests.PreparedRequest:
    request = session.prepare_request(requests.Request("GET", url))
    adapter = Mock()
    adapter.send.return_value = _build_response(request)

    with patch("requests.sessions.extract_cookies_to_jar"), \
            patch.object(session, "get_adapter", return_value=adapter):
        session.send(request, allow_redirects=False, stream=True)
    return request


class TestPerSessionPropagation(BaseTest):
    def setUp(self):
        RequestsContextPropagationManager.uninstrument()
        self.session = requests.Session()

    def tearDown(self):
        RequestsContextPropagationManager.uninstrument_session(self.session)
        RequestsContextPropagationManager.uninstrument()
        self.session.close()

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_session_injects_baggage_on_matching_url(self, _mock):
        RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS, ENABLED_HEADERS)
        request = _call_session(self.session, "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_session_injects_baggage_with_default_enabled_headers(self, _mock):
        RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS)
        request = _call_session(self.session, "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_session_accepts_request_as_keyword(self, _mock):
        request = self.session.prepare_request(
            requests.Request("GET", "http://target.example.com/path")
        )
        adapter = Mock()
        adapter.send.return_value = _build_response(request)
        RequestsContextPropagationManager.instrument_session(
            self.session,
            ENABLED_URLS,
            ENABLED_HEADERS,
        )

        with patch("requests.sessions.extract_cookies_to_jar"), \
                patch.object(self.session, "get_adapter", return_value=adapter):
            self.session.send(request=request, allow_redirects=False, stream=True)

        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_session_does_not_inject_on_non_matching_url(self, _mock):
        RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS, ENABLED_HEADERS)
        request = _call_session(self.session, "http://other.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=None)
    def test_per_session_does_not_inject_when_no_session(self, _mock):
        RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS, ENABLED_HEADERS)
        request = _call_session(self.session, "http://target.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_session_does_not_affect_uninstrumented_session(self, _mock):
        other_session = requests.Session()
        RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS, ENABLED_HEADERS)
        try:
            request = _call_session(other_session, "http://target.example.com/path")
        finally:
            other_session.close()
        self.assertIsNone(request.headers.get("baggage"))

    def test_per_session_uninstrument_removes_patch(self):
        RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS, ENABLED_HEADERS)
        RequestsContextPropagationManager.uninstrument_session(self.session)
        self.assertFalse(
            getattr(self.session, "_rollbar_requests_context_propagation_instrumented", False)
        )
        self.assertNotIn("send", vars(self.session))

    def test_per_session_uninstrument_allows_reinstrumenting_same_session(self):
        RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS, ENABLED_HEADERS)
        RequestsContextPropagationManager.uninstrument_session(self.session)

        RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS, ENABLED_HEADERS)

        self.assertTrue(
            getattr(self.session, "_rollbar_requests_context_propagation_instrumented", False)
        )

    def test_instrument_session_raises_on_double_instrument(self):
        RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS, ENABLED_HEADERS)
        with self.assertRaises(ValueError):
            RequestsContextPropagationManager.instrument_session(self.session, ENABLED_URLS, ENABLED_HEADERS)

    def test_instrumentation_does_not_keep_session_alive(self):
        session = requests.Session()
        RequestsContextPropagationManager.instrument_session(session, ENABLED_URLS, ENABLED_HEADERS)
        reference = weakref.ref(session)
        del session
        gc.collect()

        self.assertIsNone(reference())
        self.assertEqual(len(RequestsContextPropagationManager._sessions), 0)

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_session_overrides_global_and_restores_global_on_uninstrument(self, _mock):
        global_urls = [re.compile(r"^http://global\.example\.com.*")]
        RequestsContextPropagationManager.instrument(global_urls, ENABLED_HEADERS)
        RequestsContextPropagationManager.instrument_session(
            self.session,
            ENABLED_URLS,
            ENABLED_HEADERS,
        )

        global_request = _call_session(self.session, "http://global.example.com/path")
        session_request = _call_session(self.session, "http://target.example.com/path")
        self.assertIsNone(global_request.headers.get("baggage"))
        self.assertEqual(session_request.headers.get("baggage"), BAGGAGE_VALUE)

        RequestsContextPropagationManager.uninstrument_session(self.session)
        global_request = _call_session(self.session, "http://global.example.com/path")
        self.assertEqual(global_request.headers.get("baggage"), BAGGAGE_VALUE)

        RequestsContextPropagationManager.uninstrument()
        request = _call_session(self.session, "http://global.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_per_session_installed_before_global_still_takes_precedence(self, _mock):
        global_urls = [re.compile(r"^http://global\.example\.com.*")]
        RequestsContextPropagationManager.instrument_session(
            self.session,
            ENABLED_URLS,
            ENABLED_HEADERS,
        )
        RequestsContextPropagationManager.instrument(global_urls, ENABLED_HEADERS)

        global_request = _call_session(self.session, "http://global.example.com/path")
        session_request = _call_session(self.session, "http://target.example.com/path")
        self.assertIsNone(global_request.headers.get("baggage"))
        self.assertEqual(session_request.headers.get("baggage"), BAGGAGE_VALUE)

        RequestsContextPropagationManager.uninstrument_session(self.session)
        global_request = _call_session(self.session, "http://global.example.com/path")
        self.assertEqual(global_request.headers.get("baggage"), BAGGAGE_VALUE)
