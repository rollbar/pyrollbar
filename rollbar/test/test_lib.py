from rollbar.lib import dict_merge, prefix_match, key_match, key_depth
from rollbar.lib.transport import _get_proxy_cfg

from rollbar.test import BaseTest


class RollbarLibTest(BaseTest):
    def test_prefix_match(self):
        key = ['password', 'argspec', '0']
        self.assertTrue(prefix_match(key, [['password']]))

    def test_prefix_match_dont_match(self):
        key = ['environ', 'argspec', '0']
        self.assertFalse(prefix_match(key, [['password']]))

    def test_key_match(self):
        canonical = ['body', 'trace', 'frames', '*', 'locals', '*']
        key = ['body', 'trace', 'frames', 5, 'locals', 'foo']

        self.assertTrue(key_match(key, canonical))

    def test_key_match_dont_match(self):
        canonical = ['body', 'trace', 'frames', '*', 'locals', '*']
        key = ['body', 'trace', 'frames', 5, 'bar', 'foo']

        self.assertFalse(key_match(key, canonical))

    def test_key_match_wildcard_end(self):
        canonical = ['body', 'trace', 'frames', '*', 'locals', '*']
        key = ['body', 'trace', 'frames', 5, 'locals', 'foo', 'bar']

        self.assertTrue(key_match(key, canonical))

    def test_key_match_too_short(self):
        canonical = ['body', 'trace', 'frames', '*', 'locals', '*']
        key = ['body', 'trace', 'frames', 5, 'locals']

        self.assertFalse(key_match(key, canonical))

    def test_key_depth(self):
        canonicals = [['body', 'trace', 'frames', '*', 'locals', '*']]
        key = ['body', 'trace', 'frames', 5, 'locals', 'foo']

        self.assertEqual(6, key_depth(key, canonicals))

    def test_key_depth_dont_match(self):
        canonicals = [['body', 'trace', 'frames', '*', 'locals', '*']]
        key = ['body', 'trace', 'frames', 5, 'bar', 'foo']

        self.assertEqual(0, key_depth(key, canonicals))

    def test_key_depth_wildcard_end(self):
        canonicals = [['body', 'trace', 'frames', '*']]
        key = ['body', 'trace', 'frames', 5, 'locals', 'foo', 'bar']

        self.assertEqual(4, key_depth(key, canonicals))

    def test_dict_merge_not_dict(self):
        a = {'a': {'b': 42}}
        b = 99
        result = dict_merge(a, b)

        self.assertEqual(99, result)

    def test_dict_merge_dicts_independent(self):
        a = {'a': {'b': 42}}
        b = {'x': {'y': 99}}
        result = dict_merge(a, b)

        self.assertIn('a', result)
        self.assertIn('b', result['a'])
        self.assertEqual(42, result['a']['b'])
        self.assertIn('x', result)
        self.assertIn('y', result['x'])
        self.assertEqual(99, result['x']['y'])

    def test_dict_merge_dicts(self):
        a = {'a': {'b': 42}}
        b = {'a': {'c': 99}}
        result = dict_merge(a, b)

        self.assertIn('a', result)
        self.assertIn('b', result['a'])
        self.assertIn('c', result['a'])
        self.assertEqual(42, result['a']['b'])
        self.assertEqual(99, result['a']['c'])

    def test_dict_merge_dicts_second_wins(self):
        a = {'a': {'b': 42}}
        b = {'a': {'b': 99}}
        result = dict_merge(a, b)

        self.assertIn('a', result)
        self.assertIn('b', result['a'])
        self.assertEqual(99, result['a']['b'])

    def test_dict_merge_dicts_select_poll(self):
        import select
        poll = getattr(select, 'poll', None)
        if poll is None:
            return
        p = poll()
        a = {'a': {'b': 42}}
        b = {'a': {'y': p}}
        result = dict_merge(a, b, silence_errors=True)

        self.assertIn('a', result)
        self.assertIn('b', result['a'])
        self.assertEqual(42, result['a']['b'])
        self.assertIn('y', result['a'])
        self.assertRegex(result['a']['y'], r'Uncopyable obj')

    def test_transport_get_proxy_cfg(self):
        result = _get_proxy_cfg({})
        self.assertEqual(None, result)

        result = _get_proxy_cfg({'proxy': 'localhost'})
        self.assertEqual({'http': 'http://localhost', 'https': 'http://localhost'}, result)

        result = _get_proxy_cfg({'proxy': 'localhost:8080'})
        self.assertEqual({'http': 'http://localhost:8080', 'https': 'http://localhost:8080'}, result)

        result = _get_proxy_cfg({'proxy': 'localhost', 'proxy_user': 'username', 'proxy_password': 'password'})
        self.assertEqual({
            'http': 'http://username:password@localhost',
            'https': 'http://username:password@localhost',
        }, result)
