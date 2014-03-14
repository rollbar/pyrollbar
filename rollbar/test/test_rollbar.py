import copy
import json
import mock

import rollbar

from . import BaseTest

try:
    # Python 3
    import urllib.parse as urlparse
except ImportError:
    # Python 2
    import urlparse

_test_access_token = 'aaaabbbbccccddddeeeeffff00001111'
_default_settings = copy.deepcopy(rollbar.SETTINGS)


class RollbarTest(BaseTest):
    def setUp(self):
        rollbar._initialized = False
        rollbar.SETTINGS = copy.deepcopy(_default_settings)
        rollbar.init(_test_access_token)

    def test_default_configuration(self):
        self.assertEqual(rollbar.SETTINGS['access_token'], _test_access_token)
        self.assertEqual(rollbar.SETTINGS['environment'], 'production')

    @mock.patch('rollbar.send_payload')
    def test_disabled(self, send_payload):
        rollbar.SETTINGS['enabled'] = False

        rollbar.report_message('foo')
        try:
            raise Exception('foo')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, False)

    def test_server_data(self):
        server_data = rollbar._build_server_data()

        self.assertIn('host', server_data)
        self.assertIn('argv', server_data)
        self.assertNotIn('branch', server_data)
        self.assertNotIn('root', server_data)

        rollbar.SETTINGS['branch'] = 'master'
        rollbar.SETTINGS['root'] = '/home/test/'

        server_data = rollbar._build_server_data()

        self.assertIn('host', server_data)
        self.assertIn('argv', server_data)
        self.assertEqual(server_data['branch'], 'master')
        self.assertEqual(server_data['root'], '/home/test/')

    @mock.patch('rollbar.send_payload')
    def test_report_exception(self, send_payload):
        try:
            raise Exception('foo')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertEqual(payload['access_token'], _test_access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('trace', payload['data']['body'])
        self.assertIn('exception', payload['data']['body']['trace'])
        self.assertEqual(payload['data']['body']['trace']['exception']['message'], 'foo')
        self.assertEqual(payload['data']['body']['trace']['exception']['class'], 'Exception')

    @mock.patch('rollbar.send_payload')
    def test_report_messsage(self, send_payload):
        rollbar.report_message('foo')

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertEqual(payload['access_token'], _test_access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('message', payload['data']['body'])
        self.assertIn('body', payload['data']['body']['message'])
        self.assertEqual(payload['data']['body']['message']['body'], 'foo')

    def test_param_scrubbing(self):
        params = {
            'foo': 'bar',
            'bar': 'foo',
            'passwd': 'passwd',
            'password': 'password',
            'secret': 'secret',
            'confirm_password': 'confirm_password',
            'password_confirmation': 'password_confirmation'
        }

        scrubbed = rollbar._scrub_request_params(params)

        self.assertDictEqual(scrubbed, {
            'foo': 'bar',
            'bar': 'foo',
            'passwd': '******',
            'password': '********',
            'secret': '******',
            'confirm_password': '****************',
            'password_confirmation': '*********************'
        })

        rollbar.SETTINGS['scrub_fields'] = ['foo', 'password']

        scrubbed = rollbar._scrub_request_params(params)

        self.assertDictEqual(scrubbed, {
            'foo': '***',
            'bar': 'foo',
            'passwd': 'passwd',
            'password': '********',
            'secret': 'secret',
            'confirm_password': 'confirm_password',
            'password_confirmation': 'password_confirmation'
        })

    def test_url_scrubbing(self):
        url = 'http://foo.com/?password=password&foo=bar&secret=secret'

        scrubbed_url = urlparse.urlparse(rollbar._scrub_request_url(url))
        qs_params = urlparse.parse_qs(scrubbed_url.query)

        self.assertDictEqual(qs_params, {
            'password': ['--------'],
            'foo': ['bar'],
            'secret': ['------']
        })

    @mock.patch('rollbar.send_payload')
    def test_uuid(self, send_payload):
        uuid = rollbar.report_message('foo')

        payload = json.loads(send_payload.call_args[0][0])

        self.assertEqual(payload['data']['uuid'], uuid)
