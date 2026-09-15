import copy
from unittest.mock import patch

import rollbar
from tests import BaseTest


class TracingPropagationTest(BaseTest):
    def setUp(self):
        self._settings = copy.deepcopy(rollbar.SETTINGS)
        self._initialized = getattr(rollbar, '_initialized', False)
        self._agent_log = rollbar.agent_log
        rollbar._initialized = False
        rollbar.agent_log = None

    def tearDown(self):
        rollbar.SETTINGS = self._settings
        rollbar._initialized = self._initialized
        rollbar.agent_log = self._agent_log

    def test_init_calls_tracing_propagation_hooks_when_enabled(self):
        with patch.object(rollbar, '_init_httpx_propagation') as mock_httpx, \
                patch.object(rollbar, '_init_requests_propagation') as mock_requests:
            rollbar.init(
                'token',
                environment='test',
                tracing={
                    'propagation': {
                        'enabled_headers': ['baggage'],
                        'enabled_urls': ['https://example.com'],
                    },
                },
            )

        mock_httpx.assert_called_once_with()
        mock_requests.assert_called_once_with()

    def test_init_skips_tracing_hooks_when_no_propagation_configured(self):
        with patch.object(rollbar, '_init_httpx_propagation') as mock_httpx, \
                patch.object(rollbar, '_init_requests_propagation') as mock_requests:
            rollbar.init(
                'token',
                environment='test',
                tracing={
                    'propagation': {
                        'enabled_headers': [],
                        'enabled_urls': [],
                    },
                },
            )

        mock_httpx.assert_not_called()
        mock_requests.assert_not_called()

    def test_init_skips_tracing_hooks_when_no_urls_are_enabled(self):
        with patch.object(rollbar, '_init_httpx_propagation') as mock_httpx, \
                patch.object(rollbar, '_init_requests_propagation') as mock_requests:
            rollbar.init(
                'token',
                environment='test',
                tracing={
                    'propagation': {
                        'enabled_headers': ['baggage'],
                        'enabled_urls': [],
                    },
                },
            )

        mock_httpx.assert_not_called()
        mock_requests.assert_not_called()

    def test_init_skips_tracing_hooks_when_no_supported_headers_are_enabled(self):
        with patch.object(rollbar, '_init_httpx_propagation') as mock_httpx, \
                patch.object(rollbar, '_init_requests_propagation') as mock_requests:
            rollbar.init(
                'token',
                environment='test',
                tracing={
                    'propagation': {
                        'enabled_headers': ['traceparent'],
                        'enabled_urls': ['https://example.com'],
                    },
                },
            )

        mock_httpx.assert_not_called()
        mock_requests.assert_not_called()

    def test_init_requests_propagation_instruments_requests(self):
        rollbar.SETTINGS['tracing']['propagation']['enabled_headers'] = ['baggage']
        rollbar.SETTINGS['tracing']['propagation']['enabled_urls'] = ['https://example.com']

        with patch("rollbar.contrib.requests.RequestsContextPropagationManager.instrument") as mock_instrument:
            rollbar._init_requests_propagation()

        mock_instrument.assert_called_once_with(
            enabled_urls=['https://example.com'],
            enabled_headers=['baggage'],
        )
