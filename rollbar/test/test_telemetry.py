from rollbar.lib import telemetry
from rollbar.test import BaseTest
import logging
import mock
import requests


class RollbarTelemetryTest(BaseTest):

    def setUp(self):
        formatter = logging.Formatter('%(name)s :: %(levelname)s :: %(message)s')
        telemetry.set_log_telemetry(formatter)
        requests.get = telemetry.request(requests.get, False, False)

    @mock.patch('rollbar.telemetry.get_current_timestamp')
    def test_telemetry_log(self, timestamp):
        timestamp.return_value = 1000000
        logging.warning("test loggin")
        items = telemetry.TELEMETRY_QUEUE.get_items()
        self.assertEqual(1, len(items))

        result = {'body': {'message': 'root :: WARNING :: test loggin'},
                  'source': 'client', 'level': 'WARNING', 'type': 'log',
                  'timestamp_ms': 1000000}

        self.assertEqual(result, items[0])
        telemetry.TELEMETRY_QUEUE.clear_items()

    @mock.patch('rollbar.telemetry.get_current_timestamp')
    def test_telemetry_request(self, timestamp):
        timestamp.return_value = 1000000

        requests.get("http://example.com")
        items = telemetry.TELEMETRY_QUEUE.get_items()
        self.assertEqual(1, len(items))

        result = {'body': {'url': 'http://example.com', 'status_code': 200, 'method': 'get',
                           'subtype': 'http'}, 'source': 'client', 'timestamp_ms': 1000000,
                  'type': 'network', 'level': 'info'}
        self.assertEqual(result, items[0])
        telemetry.TELEMETRY_QUEUE.clear_items()
