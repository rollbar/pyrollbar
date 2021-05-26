import sys
import unittest2


def _load_tests(loader, tests, pattern):
    return unittest2.TestSuite()


if sys.version_info < (3, 5):
    load_tests = _load_tests
