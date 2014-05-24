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
        rollbar.SETTINGS['locals']['enabled'] = True
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

    def test_webob_request_data(self):
        import webob
        request = webob.Request.blank('/the/path?q=hello&password=hunter2', 
            base_url='http://example.com',
            headers={'X-Real-Ip': '5.6.7.8'},
            POST='foo=bar&confirm_password=hunter3')
        
        unscrubbed = rollbar._build_webob_request_data(request)
        self.assertEqual(unscrubbed['url'], 'http://example.com/the/path?q=hello&password=hunter2')
        self.assertEqual(unscrubbed['user_ip'], '5.6.7.8')
        self.assertDictEqual(unscrubbed['GET'], {'q': 'hello', 'password': 'hunter2'})
        self.assertDictEqual(unscrubbed['POST'], {'foo': 'bar', 'confirm_password': 'hunter3'})

        scrubbed = rollbar._scrub_request_data(unscrubbed)
        self.assertTrue(
            # order might get switched; that's ok
            scrubbed['url'] == 'http://example.com/the/path?q=hello&password=-------'
            or
            scrubbed['url'] == 'http://example.com/the/path?password=-------&q=hello'
            )
        self.assertDictEqual(unscrubbed['GET'], {'q': 'hello', 'password': '*******'})
        self.assertDictEqual(unscrubbed['POST'], {'foo': 'bar', 'confirm_password': '*******'})

    @mock.patch('rollbar.send_payload')
    def test_report_exception(self, send_payload):

        def _raise(asdf, dummy1=1, dummy2=333):
            try:
                raise Exception('foo')
            except:
                rollbar.report_exc_info()

        _raise('asdf-value')

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertEqual(payload['access_token'], _test_access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('trace', payload['data']['body'])
        self.assertIn('exception', payload['data']['body']['trace'])
        self.assertEqual(payload['data']['body']['trace']['exception']['message'], 'foo')
        self.assertEqual(payload['data']['body']['trace']['exception']['class'], 'Exception')

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('asdf', payload['data']['body']['trace']['frames'][-1]['kwargs'])
        self.assertIn('dummy1', payload['data']['body']['trace']['frames'][-1]['kwargs'])
        self.assertIn('dummy2', payload['data']['body']['trace']['frames'][-1]['kwargs'])
        self.assertEqual(payload['data']['body']['trace']['frames'][-1]['kwargs']['dummy1'], 1)
        self.assertEqual(payload['data']['body']['trace']['frames'][-1]['kwargs']['dummy2'], 333)
        self.assertEqual(payload['data']['body']['trace']['frames'][-1]['args'], ['asdf-value'])

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

        scrubbed = rollbar._scrub_obj(params)

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

        scrubbed = rollbar._scrub_obj(params)

        self.assertDictEqual(scrubbed, {
            'foo': '***',
            'bar': 'foo',
            'passwd': 'passwd',
            'password': '********',
            'secret': 'secret',
            'confirm_password': 'confirm_password',
            'password_confirmation': 'password_confirmation'
        })

    def test_json_scrubbing(self):
        params = {
            'foo': 'bar',
            'bar': {
                'foo': {
                    'password': 'password',
                    'clear': 'text'
                },
                'secret': ['1234']
            },
            'passwd': [
                {'bar': None},
                {'password': 'passwd'}
            ],
            'secret': {
                'password': {
                    'confirm_password': 'confirm_password',
                    'foo': 'bar'
                }
            },
            'password_confirmation': None,
            'confirm_password': 341254213
        }

        scrubbed = rollbar._scrub_obj(params, replacement_character='-')

        self.assertDictEqual(scrubbed, {
            'foo': 'bar',
            'bar': {
                'foo': {
                    'password': '--------',
                    'clear': 'text'
                },
                'secret': ['----']
            },
            'passwd': [{'-': '-'}, {'-': '-'}],
            'secret': {'-': '-'},
            'password_confirmation': '-',
            'confirm_password': '-'
        })

    def test_non_dict_scrubbing(self):
        params = "string"
        scrubbed = rollbar._scrub_obj(params)
        self.assertEqual(scrubbed, params)

        params = 1234
        scrubbed = rollbar._scrub_obj(params)
        self.assertEqual(scrubbed, params)

        params = None
        scrubbed = rollbar._scrub_obj(params)
        self.assertEqual(scrubbed, params)

        params = [{'password': 'password', 'foo': 'bar'}]
        scrubbed = rollbar._scrub_obj(params)
        self.assertEqual([{'password': '********', 'foo': 'bar'}], scrubbed)

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


    @mock.patch('rollbar.send_payload')
    def test_report_exc_info_level(self, send_payload):

        try:
            raise Exception('level_error')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)
        payload = json.loads(send_payload.call_args[0][0])
        self.assertEqual(payload['data']['level'], 'error')

        try:
            raise Exception('level_info')
        except:
            rollbar.report_exc_info(level='info')

        self.assertEqual(send_payload.called, True)
        payload = json.loads(send_payload.call_args[0][0])
        self.assertEqual(payload['data']['level'], 'info')

        # payload takes precendence over 'level'
        try:
            raise Exception('payload_warn')
        except:
            rollbar.report_exc_info(level='info', payload_data={'level': 'warn'})

        self.assertEqual(send_payload.called, True)
        payload = json.loads(send_payload.call_args[0][0])
        self.assertEqual(payload['data']['level'], 'warn')



    @mock.patch('rollbar.send_payload')
    def test_args_lambda_no_args(self, send_payload):

        _raise = lambda: foo()

        try:
            _raise()
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])
        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_args(self, send_payload):

        _raise = lambda arg1, arg2: foo(arg1, arg2)

        try:
            _raise('arg1-value', 'arg2-value')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])
        self.assertEqual(2, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual('arg1-value', payload['data']['body']['trace']['frames'][-1]['args'][0])
        self.assertEqual('arg2-value', payload['data']['body']['trace']['frames'][-1]['args'][1])

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_defaults(self, send_payload):

        _raise = lambda arg1='default': foo(arg1)

        try:
            _raise(arg1='arg1-value')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        # NOTE(cory): Lambdas are a bit strange. We treat default values for lambda args
        #             as positional.
        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual('arg1-value', payload['data']['body']['trace']['frames'][-1]['args'][0])

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_star_args(self, send_payload):

        _raise = lambda *args: foo(arg1)

        try:
            _raise('arg1-value')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual('arg1-value', payload['data']['body']['trace']['frames'][-1]['args'][0])

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_star_args_and_args(self, send_payload):

        _raise = lambda arg1, *args: foo(arg1)

        try:
            _raise('arg1-value', 1, 2)
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(3, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual('arg1-value', payload['data']['body']['trace']['frames'][-1]['args'][0])
        self.assertEqual(1, payload['data']['body']['trace']['frames'][-1]['args'][1])
        self.assertEqual(2, payload['data']['body']['trace']['frames'][-1]['args'][2])

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_kwargs(self, send_payload):

        _raise = lambda **args: foo(arg1)

        try:
            _raise(arg1='arg1-value', arg2=2)
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(2, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual('arg1-value', payload['data']['body']['trace']['frames'][-1]['kwargs']['arg1'])
        self.assertEqual(2, payload['data']['body']['trace']['frames'][-1]['kwargs']['arg2'])

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_kwargs_and_args(self, send_payload):

        _raise = lambda arg1, arg2, **args: foo(arg1)

        try:
            _raise('a1', 'a2', arg3='arg3-value', arg4=2)
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(2, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(2, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual('a1', payload['data']['body']['trace']['frames'][-1]['args'][0])
        self.assertEqual('a2', payload['data']['body']['trace']['frames'][-1]['args'][1])
        self.assertEqual('arg3-value', payload['data']['body']['trace']['frames'][-1]['kwargs']['arg3'])
        self.assertEqual(2, payload['data']['body']['trace']['frames'][-1]['kwargs']['arg4'])

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_kwargs_and_args_and_defaults(self, send_payload):

        _raise = lambda arg1, arg2, arg3='default-value', **args: foo(arg1)

        try:
            _raise('a1', 'a2', arg3='arg3-value', arg4=2)
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        # NOTE(cory): again, default values are strange for lambdas and we include them as
        #             positional args.
        self.assertEqual(3, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual('a1', payload['data']['body']['trace']['frames'][-1]['args'][0])
        self.assertEqual('a2', payload['data']['body']['trace']['frames'][-1]['args'][1])
        self.assertEqual('arg3-value', payload['data']['body']['trace']['frames'][-1]['args'][2])
        self.assertEqual(2, payload['data']['body']['trace']['frames'][-1]['kwargs']['arg4'])

    @mock.patch('rollbar.send_payload')
    def test_args_generators(self, send_payload):

        def _raise(arg1):
            for i in xrange(2):
                if i > 0:
                    raise Exception()
                else:
                    yield i

        try:
            l = list(_raise('hello world'))
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual('hello world', payload['data']['body']['trace']['frames'][-1]['args'][0])

    @mock.patch('rollbar.send_payload')
    def test_scrub_kwargs(self, send_payload):

        def _raise(password='sensitive', clear='text'):
            raise Exception()

        try:
            _raise()
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(2, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual('*********', payload['data']['body']['trace']['frames'][-1]['kwargs']['password'])
        self.assertEqual('text', payload['data']['body']['trace']['frames'][-1]['kwargs']['clear'])

    @mock.patch('rollbar.send_payload')
    def test_large_arg_val(self, send_payload):

        def _raise(large):
            raise Exception()

        try:
            large = ''.join(['#'] * 200)
            _raise(large)
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual("'###############################################...################################################'",
                         payload['data']['body']['trace']['frames'][-1]['args'][0])


    @mock.patch('rollbar.send_payload')
    def test_long_list_arg_val(self, send_payload):

        def _raise(large):
            raise Exception()

        try:
            large = ['hi'] * 30
            _raise(large)
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = json.loads(send_payload.call_args[0][0])

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual(0, len(payload['data']['body']['trace']['frames'][-1]['kwargs']))
        self.assertEqual("['hi', 'hi', 'hi', 'hi', 'hi', 'hi', 'hi', 'hi', 'hi', 'hi', ...]",
                         payload['data']['body']['trace']['frames'][-1]['args'][0])
