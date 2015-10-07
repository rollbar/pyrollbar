import os
import random

from rollbar.lib import build_key_matcher, text
from rollbar.lib.transforms import Transform


class ScrubTransform(Transform):
    def __init__(self, suffixes=None, redact_char='*', randomize_len=True):
        super(ScrubTransform, self).__init__()
        self.suffix_matcher = build_key_matcher(suffixes, type='suffix')
        self.redact_char = redact_char
        self.randomize_len = randomize_len

    def _in_scrub_fields(self, key):
        if not key:
            return False

        return self.suffix_matcher(key)

    def _redact(self, val):
        if self.randomize_len:
            _len = random.randint(3, 20)
        else:
            _len = len(text(val))

        return self.redact_char * _len

    def _scrub(self, val, key=None):
        if self._in_scrub_fields(key):
            return self._redact(val)

        return val

    def default(self, o, key=None):
        return self._scrub(o, key=key)

    def transform_circular_reference(self, o, key=None, ref_key=None):
        if self._in_scrub_fields(key):
            return self._redact(o)

        return super(ScrubTransform, self).transform_circular_reference(o, key=key, ref_key=ref_key)


__all__ = ['ScrubTransform']
