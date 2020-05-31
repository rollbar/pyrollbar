from rollbar.lib import dict_merge

from rollbar.test import BaseTest

class RollbarLibTest(BaseTest):
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
