import importlib
import sys

try:
    from unittest import mock
except ImportError:
    import mock

try:
    import starlette
    import rollbar.contrib.starlette

    STARLETTE_INSTALLED = True
except ImportError:
    STARLETTE_INSTALLED = False

import unittest2

import rollbar
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest2.skipUnless(
    STARLETTE_INSTALLED and ALLOWED_PYTHON_VERSION, 'Starlette requires Python3.6+'
)
class StarletteIntegrationTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar.contrib.starlette)

    def test_should_set_starlette_hook(self):
        self.assertEqual(rollbar.BASE_DATA_HOOK, rollbar.contrib.starlette._hook)

    @mock.patch('rollbar._check_config', return_value=True)
    @mock.patch('rollbar.send_payload')
    def test_should_add_starlette_version_to_payload(self, mock_send_payload, *mocks):
        import starlette

        rollbar.report_exc_info()

        mock_send_payload.assert_called_once()
        payload = mock_send_payload.call_args[0][0]

        self.assertIn(starlette.__version__, payload['data']['framework'])
