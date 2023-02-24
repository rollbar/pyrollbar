import sys
import unittest


def _load_tests(loader, tests, pattern):
    return unittest.TestSuite()


if sys.version_info < (3, 5):
    load_tests = _load_tests
