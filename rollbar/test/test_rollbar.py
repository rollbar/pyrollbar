import copy
import unittest

import rollbar


_test_access_token = 'aaaabbbbccccddddeeeeffff00001111'
_default_settings = copy.deepcopy(rollbar.SETTINGS)


class RollbarTestCase(unittest.TestCase):
    def setUp(self):
        rollbar.SETTINGS = copy.deepcopy(_default_settings)
        rollbar.init(_test_access_token)

    def test_default_environment(self):
        self.assertEqual(rollbar.SETTINGS['environment'], 'production')
