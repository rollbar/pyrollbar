import importlib
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import unittest2

import rollbar
import rollbar.contrib.fastapi
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'FastAPI requires Python3.6+')
class FastAPIIntegrationTest(BaseTest):
    def setUp(self):
        importlib.reload(rollbar.contrib.fastapi)

    def test_should_set_fastapi_hook(self):
        import rollbar.contrib.fastapi

        self.assertEqual(rollbar.BASE_DATA_HOOK, rollbar.contrib.fastapi._hook)

    @mock.patch('rollbar._check_config', return_value=True)
    @mock.patch('rollbar.send_payload')
    def test_should_add_fastapi_version_to_payload(self, mock_send_payload, *mocks):
        import fastapi
        import rollbar.contrib.fastapi

        rollbar.report_exc_info()

        mock_send_payload.assert_called_once()
        payload = mock_send_payload.call_args[0][0]

        self.assertIn(fastapi.__version__, payload['data']['framework'])
