import importlib
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import unittest2

import rollbar
import rollbar.contrib.asgi
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 5)


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'ASGI implementation requires Python3.5+')
class ASGIIntegrationTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar.contrib.asgi)

    def test_should_set_asgi_hook(self):
        self.assertEqual(rollbar.BASE_DATA_HOOK, rollbar.contrib.asgi._hook)
