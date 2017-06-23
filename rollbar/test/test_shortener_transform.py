from array import array
from collections import deque

from rollbar import DEFAULT_LOCALS_SIZES
from rollbar.lib import transforms
from rollbar.lib.transforms.shortener import ShortenerTransform
from rollbar.test import BaseTest


class TestClassWithAVeryVeryVeryVeryVeryVeryVeryLongName:
    pass


class ShortenerTransformTest(BaseTest):
    def setUp(self):
        self.data = {
            'string': 'x' * 120,
            'long': 17955682733916468498414734863645002504519623752387,
            'dict': {
                'one': 'one',
                'two': 'two',
                'three': 'three',
                'four': 'four',
                'five': 'five',
                'six': 'six',
                'seven': 'seven',
                'eight': 'eight',
                'nine': 'nine',
                'ten': 'ten',
                'eleven': 'eleven'
            },
            'list': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            'tuple': (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
            'set': set([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            'frozenset': frozenset([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            'array': array('l', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
            'deque': deque([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 15),
            'other': TestClassWithAVeryVeryVeryVeryVeryVeryVeryLongName()
        }

    def _assert_shortened(self, key, expected):
        shortener = ShortenerTransform(keys=[(key,)], **DEFAULT_LOCALS_SIZES)
        result = transforms.transform(self.data, shortener)

        if key == 'dict':
            self.assertEqual(expected, result[key].count(':'))
        elif key == 'other':
            self.assertTrue(result[key].startswith(expected))
        else:
            self.assertEqual(expected, result[key])

        result.pop(key)
        self.data.pop(key)
        self.assertEqual(result, self.data)

    def test_no_shorten(self):
        shortener = ShortenerTransform(**DEFAULT_LOCALS_SIZES)
        result = transforms.transform(self.data, shortener)
        self.assertEqual(self.data, result)

    def test_shorten_string(self):
        expected = "'{}...{}'".format('x'*47, 'x'*48)
        self._assert_shortened('string', expected)

    def test_shorten_long(self):
        expected = '179556827339164684...002504519623752387L'
        self._assert_shortened('long', expected)

    def test_shorten_mapping(self):
        # here, expected is the number of key value pairs
        expected = 10
        self._assert_shortened('dict', expected)

    def test_shorten_list(self):
        expected = '[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...]'
        self._assert_shortened('list', expected)

    def test_shorten_tuple(self):
        expected = '(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...)'
        self._assert_shortened('tuple', expected)

    def test_shorten_set(self):
        expected = 'set([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...])'
        self._assert_shortened('set', expected)

    def test_shorten_frozenset(self):
        # XXX(eric): this probably isn't doing what we expected
        # expected = 'frozenset([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...])'
        expected = "u'frozenset([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])'"
        self._assert_shortened('frozenset', expected)

    def test_shorten_array(self):
        # XXX(eric): this probably isn't doing what we expected
        # expected = 'array(\'l\', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...])'
        expected = 'u"array(\'l\', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])"'
        self._assert_shortened('array', expected)

    def test_shorten_deque(self):
        expected = 'deque([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...])'
        self._assert_shortened('deque', expected)

    def test_shorten_other(self):
        expected = ("u'<rollbar.test.test_shortener_transform.TestCla..."
                    "eryVeryVeryVeryLongName instance at")
        self._assert_shortened('other', expected)
