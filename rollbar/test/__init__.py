try:
    import unittest2 as unittest
except ImportError:
    import unittest


SNOWMAN = b'\xe2\x98\x83'
SNOWMAN_UNICODE = SNOWMAN.decode('utf8')


class BaseTest(unittest.TestCase):
    pass
