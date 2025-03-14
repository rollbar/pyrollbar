import sys
from array import array
from collections import deque

from rollbar import DEFAULT_LOCALS_SIZES, SETTINGS
from rollbar.lib import transforms
from rollbar.lib.transforms.shortener import ShortenerTransform
from rollbar.test import BaseTest


class TestClassWithAVeryVeryVeryVeryVeryVeryVeryLongName:
    pass


class KeyMemShortenerTransform(ShortenerTransform):
    """
    A shortener that just stores the keys.
    """
    keysUsed = []

    def default(self, o, key=None):
        self.keysUsed.append((key, o))
        return super(KeyMemShortenerTransform, self).default(o, key=key)


class ShortenerTransformTest(BaseTest):
    def setUp(self):
        self.shortener = ShortenerTransform(keys=[('shorten',)], **DEFAULT_LOCALS_SIZES)

    def test_shorten_string(self):
        original = 'x' * 120
        shortened = '{}...{}'.format('x'*48, 'x'*49)
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_long(self):
        original = 17955682733916468498414734863645002504519623752387
        shortened = '179556827339164684...5002504519623752387'
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_mapping(self):
        original = {
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
            }
        shortened = {
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
            }
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_bytes(self):
        original = b'\x78' * 120
        shortened = b'\x78' * 100
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_list(self):
        original = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        shortened = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, '...']
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_tuple(self):
        original = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
        shortened = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, '...')
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_set(self):
        original = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}
        shortened = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, '...'}
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_frozenset(self):
        original = frozenset([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        shortened = frozenset([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, '...'])
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_array(self):
        original = array('l', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        shortened = array('l', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_deque(self):
        original = deque([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 15)
        shortened = deque([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 15)
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_other(self):
        original = TestClassWithAVeryVeryVeryVeryVeryVeryVeryLongName()
        shortened = '<rollbar.test.test_shortener_transform.TestClas...'
        self.assertIn(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_object(self):
        data = {'request': {'POST': {i: i for i in range(12)}}}
        keys = [
                ('request', 'POST'),
                ('request', 'json'),
                ('body', 'request', 'POST'),
                ('body', 'request', 'json'),
                ]
        self.assertEqual(len(data['request']['POST']), 12)
        shortener = ShortenerTransform(keys=keys, **DEFAULT_LOCALS_SIZES)
        result = transforms.transform(data, shortener)
        self.assertEqual(type(result), dict)
        self.assertEqual(len(result['request']['POST']), 10)

    def test_shorten_custom_rollbar_repr(self):
        class CustomObj:
            value = 'value'
            def __rollbar_repr__(self):
                return f'<custom: {self.value}>'

        obj = CustomObj()

        original = obj
        shortened = '<custom: value>'
        self.assertEqual(shortened, self.shortener.default(original, ('shorten',)))
        self.assertEqual(original, self.shortener.default(original, ('nope',)))

    def test_shorten_frame(self):
        data = {
            'body': {
                'trace': {
                    'frames': [
                        {
                            "filename": "/path/to/app.py",
                            "lineno": 82,
                            "method": "sub_func",
                            "code": "extra(**kwargs)",
                            "keywordspec": "kwargs",
                            "locals": {
                                "kwargs": {
                                    "app": ["foo", "bar", "baz", "qux", "quux", "corge", "grault", "garply", "waldo",
                                            "fred", "plugh", "xyzzy", "thud"],
                                    "extra": {
                                        "request": "<class 'some.package.MyClass'>"
                                    }
                                },
                                "one": {
                                    "two": {
                                        "three": {
                                            "four": {
                                                "five": {
                                                    "six": {
                                                        "seven": 8,
                                                        "eight": "nine"
                                                    },
                                                    "ten": "Yep! this should still be here, but it is a little on the "
                                                           "long side, so we might want to cut it down a bit."
                                                }
                                            }
                                        }
                                    },
                                    "a": ["foo", "bar", "baz", "qux", 5, 6, 7, 8, 9, 10, 11, 12],
                                    "b": 14071504106566481658450568387453168916351054663,
                                    "app_id": 140715046161904,
                                    "bar": "im a bar",
                                }
                            }
                        }
                    ]
                }
            }
        }
        keys = [('body', 'trace', 'frames', '*', 'locals', '*')]
        shortener = ShortenerTransform(keys=keys, **DEFAULT_LOCALS_SIZES)
        result = transforms.transform(data, shortener)
        expected = {
            'body': {
                'trace': {
                    'frames': [
                        {
                            "filename": "/path/to/app.py",
                            "lineno": 82,
                            "method": "sub_func",
                            "code": "extra(**kwargs)",
                            "keywordspec": "kwargs",
                            "locals": {
                                "kwargs": {
                                    # Shortened
                                    "app": ['foo', 'bar', 'baz', 'qux', 'quux', 'corge', 'grault', 'garply', 'waldo',
                                           'fred', '...'],
                                    "extra": {
                                        "request": "<class 'some.package.MyClass'>"
                                    }
                                },
                                "one": {
                                    "two": {
                                        "three": {
                                            "four": {
                                                "five": {
                                                    "six": {'...': '...'},  # Dropped because it is past the maxlevel.
                                                    # Shortened
                                                    "ten": "Yep! this should still be here, but it is a litt...long "
                                                           "side, so we might want to cut it down a bit."
                                                }
                                            }
                                        }
                                    },
                                    "a": ['foo', 'bar', 'baz', 'qux', 5, 6, 7, 8, 9, 10, '...'],   # Shortened
                                    "b": '140715041065664816...7453168916351054663',  # Shortened
                                    "app_id": 140715046161904,
                                    "bar": "im a bar",
                                }
                            }
                        }
                    ]
                }
            }
        }

        self.assertEqual(result, expected)

    def test_breadth_first(self):
        obj = {
            "one": ["four", "five", 6, 7],
            "two": ("eight", "nine", "ten"),
            "three": {
                "eleven": 12,
                "thirteen": 14
            }
        }

        shortener_instance = KeyMemShortenerTransform(
            safe_repr=True,
            keys=[
                ('request', 'POST'),
                ('request', 'json'),
                ('body', 'request', 'POST'),
                ('body', 'request', 'json'),
            ],
            **SETTINGS['locals']['sizes']
        )

        transforms.transform(obj, [shortener_instance], key=())

        self.assertEqual(
            shortener_instance.keysUsed,
            [
                ((), {
                    "one": ["four", "five", 6, 7],
                    "two": ("eight", "nine", "ten"),
                    "three": {
                        "eleven": 12,
                        "thirteen": 14
                    }
                }),
                (("one",), ["four", "five", 6, 7]),
                (("one", 0), "four"),
                (("one", 1), "five"),
                (("one", 2), 6),
                (("one", 3), 7),
                (("two",), ("eight", "nine", "ten")),
                (("two", 0), "eight"),
                (("two", 1), "nine"),
                (("two", 2), "ten"),
                (("three",), {
                    "eleven": 12,
                    "thirteen": 14
                }),
                (("three", "eleven"), 12),
                (("three", "thirteen"), 14),
            ],
        )
