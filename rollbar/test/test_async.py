import sys

try:
    from unittest import mock
except ImportError:
    import mock

import unittest2

import rollbar
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'Async support requires Python3.6+')
class AsyncLibTest(BaseTest):
    def setUp(self):
        self.access_token = 'aaaabbbbccccddddeeeeffff00001111'
        rollbar._initialized = False
        rollbar.init(self.access_token, handler='async')

    @mock.patch('rollbar.send_payload')
    def test_report_exception(self, send_payload):
        from rollbar.lib._async import report_exc_info
        from rollbar.test.async_helper import run

        def _raise():
            try:
                raise Exception('foo')
            except:
                return run(report_exc_info())

        uuid = _raise()

        send_payload.assert_called_once()

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['data']['uuid'], uuid)
        self.assertEqual(payload['access_token'], self.access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('trace', payload['data']['body'])
        self.assertNotIn('trace_chain', payload['data']['body'])
        self.assertIn('exception', payload['data']['body']['trace'])
        self.assertEqual(
            payload['data']['body']['trace']['exception']['message'], 'foo'
        )
        self.assertEqual(
            payload['data']['body']['trace']['exception']['class'], 'Exception'
        )

        self.assertNotIn('argspec', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('varargspec', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('keywordspec', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('locals', payload['data']['body']['trace']['frames'][-1])

    @mock.patch('rollbar.send_payload')
    def test_report_messsage(self, send_payload):
        from rollbar.lib._async import report_message
        from rollbar.test.async_helper import run

        uuid = run(report_message('foo'))

        def r(f):
            x

        send_payload.assert_called_once()

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['data']['uuid'], uuid)
        self.assertEqual(payload['access_token'], self.access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('message', payload['data']['body'])
        self.assertIn('body', payload['data']['body']['message'])
        self.assertEqual(payload['data']['body']['message']['body'], 'foo')

    @mock.patch('rollbar.report_exc_info')
    def test_should_run_rollbar_report_exc_info(self, rollbar_report_exc_info):
        from rollbar.lib._async import report_exc_info
        from rollbar.test.async_helper import run

        try:
            raise Exception()
        except Exception:
            run(
                report_exc_info(
                    'exc_info',
                    'request',
                    'extra_data',
                    'payload_data',
                    'level_data',
                    foo='bar',
                )
            )

        rollbar_report_exc_info.assert_called_with(
            'exc_info', 'request', 'extra_data', 'payload_data', 'level_data', foo='bar'
        )

    @mock.patch('rollbar.report_message')
    def test_should_run_rollbar_report_message(self, rollbar_report_message):
        from rollbar.lib._async import report_message
        from rollbar.test.async_helper import run

        run(report_message('message', 'level', 'request', 'extra_data', 'payload_data'))

        rollbar_report_message.assert_called_with(
            'message', 'level', 'request', 'extra_data', 'payload_data'
        )
