from rollbar.lib import telemetry
from rollbar.test import BaseTest
import logging
import mock
import requests
import rollbar


try:
    # 3.x
    import urllib.request as ulib
except ImportError:
    # 2.x
    import urllib as ulib


class RollbarTelemetryTest(BaseTest):
    @classmethod
    def setUpClass(self):
        formatter = logging.Formatter('%(name)s :: %(levelname)s :: %(message)s')
        telemetry.enable_log_telemetry(formatter)
        telemetry.enable_network_telemetry(False, False)

    @mock.patch('rollbar.get_current_timestamp')
    def test_telemetry_log(self, timestamp):
        timestamp.return_value = 1000000
        logging.warning("test loggin")
        items = list(rollbar.TELEMETRY_QUEUE)
        self.assertEqual(1, len(items))

        result = {
            'body': {'message': 'root :: WARNING :: test loggin'},
            'source': 'client',
            'level': 'WARNING',
            'type': 'log',
            'timestamp_ms': 1000000,
        }

        self.assertEqual(result, items[0])
        rollbar.TELEMETRY_QUEUE.clear()

    @mock.patch('rollbar.get_current_timestamp')
    def test_telemetry_request(self, timestamp):
        timestamp.return_value = 1000000

        requests.get("http://example.com")
        items = list(rollbar.TELEMETRY_QUEUE)
        self.assertEqual(1, len(items))

        result = {
            'body': {
                'url': 'http://example.com',
                'status_code': 200,
                'method': 'GET',
                'subtype': 'http',
            },
            'source': 'client',
            'timestamp_ms': 1000000,
            'type': 'network',
            'level': 'info',
        }
        self.assertEqual(result, items[0])
        rollbar.TELEMETRY_QUEUE.clear()

    @mock.patch('rollbar.get_current_timestamp')
    def test_telemetry_urllib_request(self, timestamp):
        timestamp.return_value = 1000000

        ulib.urlopen("http://example.com")
        items = list(rollbar.TELEMETRY_QUEUE)
        self.assertEqual(1, len(items))

        result = {
            'body': {
                'url': 'http://example.com',
                'status_code': 200,
                'method': 'GET',
                'subtype': 'http',
            },
            'source': 'client',
            'timestamp_ms': 1000000,
            'type': 'network',
            'level': 'info',
        }
        self.assertEqual(result, items[0])
        rollbar.TELEMETRY_QUEUE.clear()
