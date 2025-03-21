import collections
import base64
import copy
import enum
import sys

from collections.abc import Mapping

from rollbar.lib import transforms
from rollbar.lib.transforms.serializable import SerializableTransform

from rollbar.test import BaseTest, SNOWMAN_UNICODE

SNOWMAN_LEN = len(SNOWMAN_UNICODE)


# This base64 encoded string contains bytes that do not
# convert to utf-8 data
invalid_b64 = b'CuX2JKuXuLVtJ6l1s7DeeQ=='

invalid = base64.b64decode(invalid_b64)
undecodable_repr = f'<Undecodable type:({"bytes"}) base64:({invalid_b64.decode("ascii")})>'


class SerializableTransformTest(BaseTest):
    def _assertSerialized(self, start, expected, safe_repr=True, safelist=None, skip_id_check=False):
        serializable = SerializableTransform(safe_repr=safe_repr, safelist_types=safelist)
        result = transforms.transform(start, serializable)

        """
        #print start
        print result
        print expected
        """

        if not skip_id_check:
            self.assertNotEqual(id(result), id(expected))

        self.assertEqual(type(expected), type(result))

        if isinstance(result, Mapping):
            self.assertDictEqual(result, expected)
        elif isinstance(result, tuple):
            self.assertTupleEqual(result, expected)
        elif isinstance(result, (list, set)):
            self.assertListEqual(result, expected)
        else:
            self.assertEqual(result, expected)

    def test_simple_dict(self):
        start = {
            'hello': 'world',
            '1': 2,
        }
        expected = copy.deepcopy(start)
        self._assertSerialized(start, expected)

    def test_enum(self):
        class EnumTest(enum.Enum):
            one = 1
            two = 2

        start = EnumTest.one
        expected = "<enum 'EnumTest'>"
        self._assertSerialized(start, expected)

    def test_enum_no_safe_repr(self):
        class EnumTest(enum.Enum):
            one = 1
            two = 2

        start = EnumTest.one
        expected = '<EnumTest.one: 1>'
        self._assertSerialized(start, expected, safe_repr=False)

    def test_int_enum(self):
        class EnumTest(enum.IntEnum):
            one = 1
            two = 2

        start = EnumTest.one
        expected = "<enum 'EnumTest'>"
        self._assertSerialized(start, expected)

    def test_int_enum_no_safe_repr(self):
        class EnumTest(enum.IntEnum):
            one = 1
            two = 2

        start = EnumTest.one
        expected = '<EnumTest.one: 1>'
        self._assertSerialized(start, expected, safe_repr=False)

    def test_encode_dict_with_invalid_utf8(self):
        start = {
            'invalid': invalid
        }
        expected = copy.copy(start)
        expected['invalid'] = undecodable_repr
        self._assertSerialized(start, expected)

    def test_encode_utf8(self):
        start = invalid
        expected = undecodable_repr
        self._assertSerialized(start, expected)

    def test_encode_None(self):
        start = None
        expected = None
        self._assertSerialized(start, expected, skip_id_check=True)

    def test_encode_float(self):
        start = 3.14
        expected = 3.14
        self._assertSerialized(start, expected, skip_id_check=True)

    def test_encode_float_nan(self):
        start = float('nan')
        expected = '<NaN>'
        self._assertSerialized(start, expected, skip_id_check=True)

    def test_encode_float_infinity(self):
        start = float('inf')
        expected = '<Infinity>'
        self._assertSerialized(start, expected, skip_id_check=True)

    def test_encode_float_neg_infinity(self):
        start = float('-inf')
        expected = '<NegativeInfinity>'
        self._assertSerialized(start, expected, skip_id_check=True)

    def test_encode_int(self):
        start = 33
        expected = 33
        self._assertSerialized(start, expected, skip_id_check=True)

    def test_encode_empty_tuple(self):
        start = ()
        expected = ()
        
        skip_id_check = False
        # different behavior in 3.11
        if sys.version_info >= (3, 11):
            skip_id_check = True
        
        self._assertSerialized(start, expected, skip_id_check=skip_id_check)

    def test_encode_empty_list(self):
        start = []
        expected = []
        self._assertSerialized(start, expected)

    def test_encode_empty_dict(self):
        start = {}
        expected = {}
        self._assertSerialized(start, expected)

    def test_encode_namedtuple(self):
        MyType = collections.namedtuple('MyType', ('field_1', 'field_2'))
        nt = MyType(field_1='this is field 1', field_2=invalid)

        start = nt
        expected = "<MyType(field_1='this is field 1', field_2='%s')>" % undecodable_repr

        self._assertSerialized(start, expected)

    def test_encode_tuple_with_bytes(self):
        start = ('hello', 'world', invalid)
        expected = list(start)
        expected[2] = undecodable_repr
        self._assertSerialized(start, tuple(expected))

    def test_encode_list_with_bytes(self):
        start = ['hello', 'world', invalid]
        expected = list(start)
        expected[2] = undecodable_repr
        self._assertSerialized(start, expected)

    def test_encode_dict_with_bytes(self):
        start = {'hello': 'world', 'invalid': invalid}
        expected = copy.deepcopy(start)
        expected['invalid'] = undecodable_repr
        self._assertSerialized(start, expected)

    def test_encode_dict_with_bytes_key(self):
        start = {'hello': 'world', invalid: 'works?'}
        expected = copy.deepcopy(start)
        expected[undecodable_repr] = 'works?'
        del expected[invalid]
        self._assertSerialized(start, expected)

    def test_encode_with_rollbar_repr(self):
        class CustomRepr(object):
            def __rollbar_repr__(self):
                return 'hello'

        start = {'hello': 'world', 'custom': CustomRepr()}
        expected = copy.deepcopy(start)
        expected['custom'] = 'hello'
        self._assertSerialized(start, expected)

    def test_encode_with_custom_repr_no_safelist(self):
        class CustomRepr(object):
            def __repr__(self):
                return 'hello'

        start = {'hello': 'world', 'custom': CustomRepr()}
        expected = copy.deepcopy(start)
        expected['custom'] = str(CustomRepr)
        self._assertSerialized(start, expected)

    def test_encode_with_custom_repr_no_safelist_no_safe_repr(self):
        class CustomRepr(object):
            def __repr__(self):
                return 'hello'

        start = {'hello': 'world', 'custom': CustomRepr()}
        expected = copy.deepcopy(start)
        expected['custom'] = 'hello'
        self._assertSerialized(start, expected, safe_repr=False)

    def test_encode_with_custom_repr_safelist(self):
        class CustomRepr(object):
            def __repr__(self):
                return 'hello'

        start = {'hello': 'world', 'custom': CustomRepr()}
        expected = copy.deepcopy(start)
        expected['custom'] = 'hello'
        self._assertSerialized(start, expected, safelist=[CustomRepr])

    def test_encode_with_custom_repr_returns_bytes(self):
        class CustomRepr(object):
            def __repr__(self):
                return b'hello'

        start = {'hello': 'world', 'custom': CustomRepr()}

        serializable = SerializableTransform(safelist_types=[CustomRepr])
        result = transforms.transform(start, serializable)

        self.assertRegex(result['custom'], "<class '.*CustomRepr'>")

    def test_encode_with_custom_repr_returns_object(self):
        class CustomRepr(object):
            def __repr__(self):
                return {'hi': 'there'}

        start = {'hello': 'world', 'custom': CustomRepr()}

        serializable = SerializableTransform(safelist_types=[CustomRepr])
        result = transforms.transform(start, serializable)
        self.assertRegex(result['custom'], "<class '.*CustomRepr'>")

    def test_encode_with_custom_repr_returns_unicode(self):
        class CustomRepr(object):
            def __repr__(self):
                return SNOWMAN_UNICODE

        start = {'hello': 'world', 'custom': CustomRepr()}
        expected = copy.deepcopy(start)
        expected['custom'] = SNOWMAN_UNICODE
        self._assertSerialized(start, expected, safelist=[CustomRepr])

    def test_encode_with_bad_repr_doesnt_die(self):
        class CustomRepr(object):
            def __repr__(self):
                assert False

        start = {'hello': 'world', 'custom': CustomRepr()}
        serializable = SerializableTransform(safelist_types=[CustomRepr])
        result = transforms.transform(start, serializable)
        self.assertRegex(result['custom'], "<AssertionError.*CustomRepr.*>")

    def test_encode_with_bad_str_doesnt_die(self):

        class UnStringableException(Exception):
            def __str__(self):
                raise Exception('asdf')

        class CustomRepr(object):

            def __repr__(self):
                raise UnStringableException()

        start = {'hello': 'world', 'custom': CustomRepr()}
        serializable = SerializableTransform(safelist_types=[CustomRepr])
        result = transforms.transform(start, serializable)
        self.assertRegex(result['custom'], "<UnStringableException.*Exception.*str.*>")
