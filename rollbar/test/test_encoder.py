"""
Tests for the ErrorIgnoringJSONEncoder
"""
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
        start = {
            'invalid': "\n\xe5\xf6$\xab\x97\xb8\xb5m'\xa9u\xb3\xb0\xdey",
        }
        encoder = ErrorIgnoringJSONEncoder()
        encoded = encoder.encode(start)
        decoded = json.loads(encoded)

        self.assertDictEqual(start, decoded)
