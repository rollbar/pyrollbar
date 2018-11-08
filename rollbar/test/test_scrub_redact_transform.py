try:
    # Python 3
    from collections.abc import Mapping
except ImportError:
    # Python 2.7
    from collections import Mapping

from rollbar.lib import text, transforms
from rollbar.lib.transforms.scrub_redact import ScrubRedactTransform, REDACT_REF

from rollbar.test import BaseTest


class NotRedactRef():
    pass

NOT_REDACT_REF = NotRedactRef()

try:
    SCRUBBED = '*' * len(REDACT_REF)
except:
    SCRUBBED = '*' * len(text(REDACT_REF))


class ScrubRedactTransformTest(BaseTest):
    def _assertScrubbed(self, start, expected, redact_char='*', skip_id_check=False):
        scrubber = ScrubRedactTransform(redact_char=redact_char, randomize_len=False)
        result = transforms.transform(start, scrubber)

        if not skip_id_check:
            self.assertNotEqual(id(result), id(expected))

        self.assertEqual(type(result), type(expected))

        if isinstance(result, Mapping):
            self.assertDictEqual(result, expected)
        elif isinstance(result, tuple):
            self.assertTupleEqual(result, expected)
        elif isinstance(result, list):
            self.assertListEqual(result, expected)
        elif isinstance(result, set):
            self.assertSetEqual(result, expected)
        else:
            self.assertEqual(result, expected)

    def test_no_scrub(self):
        obj = NOT_REDACT_REF
        expected = NOT_REDACT_REF
        self._assertScrubbed(obj, expected, skip_id_check=True)

    def test_scrub(self):
        obj = REDACT_REF
        expected = SCRUBBED
        self._assertScrubbed(obj, expected)

    def test_scrub_list(self):
        obj = [REDACT_REF, REDACT_REF, REDACT_REF]
        expected = [SCRUBBED, SCRUBBED, SCRUBBED]
        self._assertScrubbed(obj, expected)

    def test_scrub_set(self):
        obj = set([REDACT_REF, NOT_REDACT_REF])
        expected = set([SCRUBBED, NOT_REDACT_REF])
        self._assertScrubbed(obj, expected)

    def scrub_tuple(self):
        obj = (REDACT_REF, REDACT_REF, REDACT_REF)
        expected = (SCRUBBED, SCRUBBED, SCRUBBED)
        self._assertScrubbed(obj, expected)

    def test_scrub_dict(self):
        obj = {'scrub_me': REDACT_REF}
        expected = {'scrub_me': SCRUBBED}
        self._assertScrubbed(obj, expected)
