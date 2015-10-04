"""
Tests for the ErrorIgnoringJSONEncoder
"""
import base64
import json

from rollbar import ErrorIgnoringJSONEncoder

from rollbar.test import BaseTest


class ErrorIgnoringJSONEncoderTest(BaseTest):

    def test_encode_simple_dict(self):
        start = {
            'hello': 'world',
            '1': 2,
        }
        encoder = ErrorIgnoringJSONEncoder()
        encoded = encoder.encode(start)
        decoded = json.loads(encoded)

        self.assertDictEqual(start, decoded)

    def test_encode_dict_with_invalid_utf8(self):
        # This base64 encoded string contains bytes that do not
        # convert to utf-8 data
        invalid_b64 = 'CuX2JKuXuLVtJ6l1s7DeeQ=='
        invalid = base64.b64decode(invalid_b64)

        start = {
            'invalid': invalid
        }
        encoder = ErrorIgnoringJSONEncoder()
        encoded = encoder.encode(start)
        decoded = json.loads(encoded)

        self.assertIn('invalid', decoded)
        self.assertIn('Undecodable', decoded['invalid'])
        self.assertIn('invalid continuation byte', decoded['invalid'])
