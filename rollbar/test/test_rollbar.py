import copy
import mock
import urllib

import rollbar

from . import BaseTest

try:
    # Python 3
    import urllib.parse as urlparse
    urllibquote = urlparse.quote
except ImportError:
    # Python 2
    import urlparse
    import urllib
    urllibquote = urllib.quote

_test_access_token = 'aaaabbbbccccddddeeeeffff00001111'
_default_settings = copy.deepcopy(rollbar.SETTINGS)

SNOWMAN = '\xe2\x98\x83'

class RollbarTest(BaseTest):
    def setUp(self):
        rollbar._initialized = False
        rollbar.SETTINGS = copy.deepcopy(_default_settings)
        rollbar.init(_test_access_token, locals={'enabled': True}, dummy_key='asdf', timeout=12345)

    def test_merged_settings(self):
        self.assertDictEqual(rollbar.SETTINGS['locals'], {'enabled': True, 'sizes': rollbar.DEFAULT_LOCALS_SIZES})
        self.assertEqual(rollbar.SETTINGS['timeout'], 12345)
        self.assertEqual(rollbar.SETTINGS['dummy_key'], 'asdf')

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

        def _raise():
            try:
                raise Exception('foo')
            except:
                rollbar.report_exc_info()

        _raise()

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['access_token'], _test_access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('trace', payload['data']['body'])
        self.assertIn('exception', payload['data']['body']['trace'])
        self.assertEqual(payload['data']['body']['trace']['exception']['message'], 'foo')
        self.assertEqual(payload['data']['body']['trace']['exception']['class'], 'Exception')

        self.assertNotIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])

    @mock.patch('rollbar.send_payload')
    def test_report_messsage(self, send_payload):
        rollbar.report_message('foo')

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

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
            'confirm_password': 341254213,
            333: 444
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
            'confirm_password': '-',
            333: 444
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

    def test_utf8_url_val_scrubbing(self):
        url = 'http://foo.com/?password=password&foo=bar&secret=%s' % SNOWMAN

        scrubbed_url = urlparse.urlparse(rollbar._scrub_request_url(url))
        qs_params = urlparse.parse_qs(scrubbed_url.query)

        self.assertDictEqual(qs_params, {
            'password': ['--------'],
            'foo': ['bar'],
            'secret': [''.join(['-'] * len(SNOWMAN))]
        })


    def test_utf8_url_key_scrubbing(self):
        url = 'http://foo.com/?password=password&foo=bar&%s=secret' % urllibquote(SNOWMAN)

        rollbar.SETTINGS['scrub_fields'].append(SNOWMAN)
        scrubbed_url = rollbar._scrub_request_url(url)

        qs_params = urlparse.parse_qs(urlparse.urlparse(scrubbed_url).query)

        self.assertEqual(['------'], qs_params[SNOWMAN])
        self.assertEqual(['--------'], qs_params['password'])
        self.assertEqual(['bar'], qs_params['foo'])


    def test_unicode_val_scrubbing(self):
        s = '%s is a unicode snowman!' % SNOWMAN
        obj = {
            'password': s
        }

        scrubbed = rollbar._scrub_obj(obj)

        self.assertDictEqual(scrubbed, {
            'password': ''.join(['*'] * len(s))
        })

    def test_unicode_key_scrubbing(self):
        s = 'is a unicode snowman!'
        obj = {
            SNOWMAN: s
        }

        rollbar.SETTINGS['scrub_fields'].append(SNOWMAN)
        scrubbed = rollbar._scrub_obj(obj)

        self.assertDictEqual(scrubbed, {
            SNOWMAN: ''.join(['*'] * len(s))
        })

        obj2 = {
            SNOWMAN: s
        }

        rollbar.SETTINGS['scrub_fields'].pop()
        rollbar.SETTINGS['scrub_fields'].append(SNOWMAN)
        scrubbed = rollbar._scrub_obj(obj2)

        self.assertDictEqual(scrubbed, {
            SNOWMAN: ''.join(['*'] * len(s))
        })

    @mock.patch('rollbar.send_payload')
    def test_uuid(self, send_payload):
        uuid = rollbar.report_message('foo')

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['data']['uuid'], uuid)


    @mock.patch('rollbar.send_payload')
    def test_report_exc_info_level(self, send_payload):

        try:
            raise Exception('level_error')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)
        payload = send_payload.call_args[0][0]
        self.assertEqual(payload['data']['level'], 'error')

        try:
            raise Exception('level_info')
        except:
            rollbar.report_exc_info(level='info')

        self.assertEqual(send_payload.called, True)
        payload = send_payload.call_args[0][0]
        self.assertEqual(payload['data']['level'], 'info')

        # payload takes precendence over 'level'
        try:
            raise Exception('payload_warn')
        except:
            rollbar.report_exc_info(level='info', payload_data={'level': 'warn'})

        self.assertEqual(send_payload.called, True)
        payload = send_payload.call_args[0][0]
        self.assertEqual(payload['data']['level'], 'warn')

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_no_args(self, send_payload):

        _raise = lambda: foo()

        try:
            _raise()
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

        self.assertNotIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_args(self, send_payload):

        _raise = lambda arg1, arg2: foo(arg1, arg2)

        try:
            _raise('arg1-value', 'arg2-value')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])
        self.assertEqual(2, len(payload['data']['body']['trace']['frames'][-1]['args']))
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

        payload = send_payload.call_args[0][0]

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        # NOTE(cory): Lambdas are a bit strange. We treat default values for lambda args
        #             as positional.
        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual('arg1-value', payload['data']['body']['trace']['frames'][-1]['args'][0])

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_star_args(self, send_payload):

        _raise = lambda *args: foo(arg1)

        try:
            _raise('arg1-value')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual('arg1-value', payload['data']['body']['trace']['frames'][-1]['args'][0])

    @mock.patch('rollbar.send_payload')
    def test_args_lambda_with_star_args_and_args(self, send_payload):

        _raise = lambda arg1, *args: foo(arg1)

        try:
            _raise('arg1-value', 1, 2)
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(3, len(payload['data']['body']['trace']['frames'][-1]['args']))
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

        payload = send_payload.call_args[0][0]

        self.assertNotIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

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

        payload = send_payload.call_args[0][0]

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

        payload = send_payload.call_args[0][0]

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

        payload = send_payload.call_args[0][0]

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
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

        payload = send_payload.call_args[0][0]

        self.assertNotIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('kwargs', payload['data']['body']['trace']['frames'][-1])

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

        payload = send_payload.call_args[0][0]

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
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

        payload = send_payload.call_args[0][0]

        self.assertIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertEqual(1, len(payload['data']['body']['trace']['frames'][-1]['args']))
        self.assertEqual("['hi', 'hi', 'hi', 'hi', 'hi', 'hi', 'hi', 'hi', 'hi', 'hi', ...]",
                         payload['data']['body']['trace']['frames'][-1]['args'][0])


    @mock.patch('rollbar.send_payload')
    def test_last_frame_has_locals(self, send_payload):

        def _raise():
            some_var = 'some value'
            raise Exception()

        try:
            _raise()
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

        self.assertNotIn('args', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('kwargs', payload['data']['body']['trace']['frames'][-1])

        self.assertIn('locals', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('some_var', payload['data']['body']['trace']['frames'][-1]['locals'])
        self.assertEqual("some value",
                         payload['data']['body']['trace']['frames'][-1]['locals']['some_var'])


    @mock.patch('rollbar.send_payload')
    def test_all_project_frames_have_locals(self, send_payload):

        prev_root = rollbar.SETTINGS['root']
        rollbar.SETTINGS['root'] = __file__.rstrip('pyc')
        try:
            step1()
        except:
            rollbar.report_exc_info()
        finally:
            rollbar.SETTINGS['root'] = prev_root

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

        for frame in payload['data']['body']['trace']['frames']:
            self.assertIn('locals', frame)


    @mock.patch('rollbar.send_payload')
    def test_only_last_frame_has_locals(self, send_payload):

        prev_root = rollbar.SETTINGS['root']
        rollbar.SETTINGS['root'] = 'dummy'
        try:
            step1()
        except:
            rollbar.report_exc_info()
        finally:
            rollbar.SETTINGS['root'] = prev_root

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

        num_frames = len(payload['data']['body']['trace']['frames'])
        for i, frame in enumerate(payload['data']['body']['trace']['frames']):
            if i < num_frames - 1:
                self.assertNotIn('locals', frame)
            else:
                self.assertIn('locals', frame)


    @mock.patch('rollbar.send_payload')
    def test_modify_arg(self, send_payload):
        # Record locals for all frames
        prev_root = rollbar.SETTINGS['root']
        rollbar.SETTINGS['root'] = __file__.rstrip('pyc')
        try:
            called_with('original value')
        except:
            rollbar.report_exc_info()
        finally:
            rollbar.SETTINGS['root'] = prev_root

        self.assertEqual(send_payload.called, True)

        payload = send_payload.call_args[0][0]

        frames = payload['data']['body']['trace']['frames']
        called_with_frame = frames[1]
        
        self.assertEqual('changed', called_with_frame['args'][0])



### Helpers

def step1():
    val1 = 1
    step2()


def step2():
    val2 = 2
    raise Exception()


def called_with(arg1):
    arg1 = 'changed'
    step1()
