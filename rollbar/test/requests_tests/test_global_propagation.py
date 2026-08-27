import re
import requests

from functools import wraps
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


def _call_session(
        session: requests.Session,
        url: str,
        *,
        headers=None,
        request_as_keyword=False,
) -> requests.PreparedRequest:
    request = session.prepare_request(requests.Request("GET", url, headers=headers))
    adapter = Mock()
    adapter.send.return_value = _build_response(request)

    with patch("requests.sessions.extract_cookies_to_jar"), \
            patch.object(session, "get_adapter", return_value=adapter):
        if request_as_keyword:
            session.send(request=request, allow_redirects=False, stream=True)
        else:
            session.send(request, allow_redirects=False, stream=True)
    adapter.send.assert_called_once()
    return request


class _RedirectAdapter(requests.adapters.BaseAdapter):
    def __init__(self):
        self.requests = []

    def send(self, request, **kwargs):
        self.requests.append(request.copy())
        response = _build_response(request)
        if len(self.requests) == 1:
            response.status_code = 302
            response.headers["location"] = "http://outside.example.com/landing"
        return response

    def close(self):
        pass


class TestGlobalPropagation(BaseTest):
    def setUp(self):
        RequestsContextPropagationManager.uninstrument()

    def tearDown(self):
        RequestsContextPropagationManager.uninstrument()

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_injects_baggage_on_matching_url(self, _mock):
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = _call_session(requests.Session(), "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_injects_baggage_on_exact_url_match(self, _mock):
        RequestsContextPropagationManager.instrument(["http://target.example.com/path"], ENABLED_HEADERS)
        request = _call_session(requests.Session(), "http://target.example.com/path")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_normalizes_exact_root_url(self, _mock):
        RequestsContextPropagationManager.instrument(["http://target.example.com"], ENABLED_HEADERS)
        request = _call_session(requests.Session(), "http://target.example.com")
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_accepts_request_as_keyword(self, _mock):
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = _call_session(
            requests.Session(),
            "http://target.example.com/path",
            request_as_keyword=True,
        )
        self.assertEqual(request.headers.get("baggage"), BAGGAGE_VALUE)

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_preserves_non_rollbar_baggage(self, _mock):
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = _call_session(
            requests.Session(),
            "http://target.example.com/path",
            headers={"baggage": "vendor.key=value, rollbar.session.id=stale"},
        )
        self.assertEqual(
            request.headers.get("baggage"),
            f"vendor.key=value, {BAGGAGE_VALUE}",
        )

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_does_not_inject_on_non_matching_url(self, _mock):
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = _call_session(requests.Session(), "http://other.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_removes_only_rollbar_baggage_from_non_matching_url(self, _mock):
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = _call_session(
            requests.Session(),
            "http://other.example.com/path",
            headers={"baggage": "vendor.key=value, rollbar.session.id=stale"},
        )
        self.assertEqual(request.headers.get("baggage"), "vendor.key=value")

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_removes_rollbar_baggage_on_disallowed_redirect(self, _mock):
        session = requests.Session()
        adapter = _RedirectAdapter()
        session.mount("http://", adapter)
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        try:
            session.get("http://target.example.com/path")
        finally:
            session.close()

        self.assertEqual(adapter.requests[0].headers.get("baggage"), BAGGAGE_VALUE)
        self.assertIsNone(adapter.requests[1].headers.get("baggage"))

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=None)
    def test_global_does_not_inject_when_no_session(self, _mock):
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        request = _call_session(requests.Session(), "http://target.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))

    @patch(
        "rollbar.contrib.requests.get_propagation_header",
        side_effect=RuntimeError("propagation failed"),
    )
    def test_global_sends_request_when_injection_fails(self, _mock):
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)

        with self.assertLogs("rollbar.contrib.requests", level="ERROR") as logs:
            request = _call_session(requests.Session(), "http://target.example.com/path")

        self.assertIsNone(request.headers.get("baggage"))
        self.assertEqual(
            logs.output,
            [
                "ERROR:rollbar.contrib.requests:Error injecting Rollbar "
                "propagation headers into request: propagation failed"
            ],
        )

    @patch("rollbar.contrib.requests.get_propagation_header", return_value=BAGGAGE_VALUE)
    def test_global_honors_enabled_headers(self, _mock):
        RequestsContextPropagationManager.instrument(["http://target.example.com/path"], ["traceparent"])
        request = _call_session(requests.Session(), "http://target.example.com/path")
        self.assertIsNone(request.headers.get("baggage"))
        self.assertIsNone(request.headers.get("traceparent"))

    def test_global_uninstrument_removes_patch(self):
        original_send = requests.Session.send
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        RequestsContextPropagationManager.uninstrument()
        self.assertFalse(RequestsContextPropagationManager._globally_instrumented)
        self.assertIs(requests.Session.send, original_send)

    def test_global_uninstrument_preserves_later_wrapper(self):
        original_send = requests.Session.send
        RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)

        @wraps(requests.Session.send)
        def other_wrapper(session, request, **kwargs):
            return other_wrapper.__wrapped__(session, request, **kwargs)

        requests.Session.send = other_wrapper
        try:
            RequestsContextPropagationManager.uninstrument()
            self.assertIs(requests.Session.send, other_wrapper)
        finally:
            requests.Session.send = original_send

    def test_global_skips_requests_without_session_send(self):
        with patch("rollbar.contrib.requests.Session", object):
            RequestsContextPropagationManager.instrument(ENABLED_URLS, ENABLED_HEADERS)
        self.assertFalse(RequestsContextPropagationManager._globally_instrumented)
