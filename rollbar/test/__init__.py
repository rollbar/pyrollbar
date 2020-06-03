import unittest


SNOWMAN = b'\xe2\x98\x83'
SNOWMAN_UNICODE = SNOWMAN.decode('utf8')


class BaseTest(unittest.TestCase):
    pass


def discover():
    return unittest2.defaultTestLoader.discover(__name__)
