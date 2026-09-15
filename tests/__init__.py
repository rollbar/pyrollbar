import unittest


SNOWMAN = b'\xe2\x98\x83'
SNOWMAN_UNICODE = SNOWMAN.decode('utf8')


class BaseTest(unittest.TestCase):
    pass


def discover():
    loader = unittest.TestLoader()
    suite = loader.discover(__name__)
    return suite
