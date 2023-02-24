import unittest
import sys


SNOWMAN = b'\xe2\x98\x83'
SNOWMAN_UNICODE = SNOWMAN.decode('utf8')


class BaseTest(unittest.TestCase):
    pass


class SkipAsyncTestLoader(unittest.TestLoader):
    """
    Python 2 does not have the async keyword, so when tests are run under python 2.7 the loader
    will fail with a syntaxerror. This loader class does the following:
    - try to load as normal
    - if loading fails because of a syntax error in python < 3.4, skip the file.
    """
    def _get_module_from_name(self, name):
        try:
            return super(SkipAsyncTestLoader, self)._get_module_from_name(name)
        except SyntaxError as e:
            if sys.version_info < (3, 5):
                return None
            else:
                raise


def discover():
    loader = SkipAsyncTestLoader()
    suite = loader.discover(__name__)
    return suite
