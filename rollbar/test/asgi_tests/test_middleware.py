import copy
import importlib
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import unittest2

import rollbar
import rollbar.contrib.asgi
from rollbar.lib._async import AsyncMock
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 5)


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'ASGI implementation requires Python3.5+')
class ReporterMiddlewareTest(BaseTest):
    default_settings = copy.deepcopy(rollbar.SETTINGS)

    def setUp(self):
        rollbar.SETTINGS = copy.deepcopy(self.default_settings)
        rollbar.SETTINGS['handler'] = 'async'
        importlib.reload(rollbar.contrib.asgi)

    @mock.patch('rollbar.report_exc_info')
    def test_should_catch_and_report_errors(self, mock_report):
        from rollbar.contrib.asgi.middleware import ReporterMiddleware
        from rollbar.lib._async import FailingTestASGIApp, run

        testapp = ReporterMiddleware(FailingTestASGIApp())

        with self.assertRaises(RuntimeError):
            run(testapp({'type': 'http'}, None, None))

        mock_report.assert_called_once()

        args, kwargs = mock_report.call_args
        self.assertEqual(kwargs, {})

        exc_type, exc_value, exc_tb = args[0]

        self.assertEqual(exc_type, RuntimeError)
        self.assertIsInstance(exc_value, RuntimeError)

    @mock.patch('rollbar.lib._async.report_exc_info', new_callable=AsyncMock)
    @mock.patch('rollbar.report_exc_info')
    def test_should_use_async_report_exc_info_if_default_handler(
        self, sync_report_exc_info, async_report_exc_info
    ):
        import rollbar
        from rollbar.contrib.asgi.middleware import ReporterMiddleware
        from rollbar.lib._async import FailingTestASGIApp, run

        rollbar.SETTINGS['handler'] = 'default'
        testapp = ReporterMiddleware(FailingTestASGIApp())

        with self.assertRaises(RuntimeError):
            run(testapp({'type': 'http'}, None, None))

        async_report_exc_info.assert_called_once()
        sync_report_exc_info.assert_not_called()

    @mock.patch('rollbar.lib._async.report_exc_info', new_callable=AsyncMock)
    @mock.patch('rollbar.report_exc_info')
    def test_should_use_async_report_exc_info_if_any_async_handler(
        self, sync_report_exc_info, async_report_exc_info
    ):
        import rollbar
        from rollbar.contrib.asgi.middleware import ReporterMiddleware
        from rollbar.lib._async import FailingTestASGIApp, run

        rollbar.SETTINGS['handler'] = 'httpx'
        testapp = ReporterMiddleware(FailingTestASGIApp())

        with self.assertRaises(RuntimeError):
            run(testapp({'type': 'http'}, None, None))

        async_report_exc_info.assert_called_once()
        sync_report_exc_info.assert_not_called()

    @mock.patch('rollbar.lib._async.report_exc_info', new_callable=AsyncMock)
    @mock.patch('rollbar.report_exc_info')
    def test_should_use_sync_report_exc_info_if_non_async_handlers(
        self, sync_report_exc_info, async_report_exc_info
    ):
        import rollbar
        from rollbar.contrib.asgi.middleware import ReporterMiddleware
        from rollbar.lib._async import FailingTestASGIApp, run

        rollbar.SETTINGS['handler'] = 'threading'
        testapp = ReporterMiddleware(FailingTestASGIApp())

        with self.assertRaises(RuntimeError):
            run(testapp({'type': 'http'}, None, None))

        sync_report_exc_info.assert_called_once()
        async_report_exc_info.assert_not_called()

    def test_should_support_http_only(self):
        from rollbar.contrib.asgi.middleware import ReporterMiddleware
        from rollbar.lib._async import FailingTestASGIApp, run

        testapp = ReporterMiddleware(FailingTestASGIApp())

        with mock.patch('rollbar.report_exc_info') as mock_report:
            with self.assertRaises(RuntimeError):
                run(testapp({'type': 'http'}, None, None))

            mock_report.assert_called_once()

        with mock.patch('rollbar.report_exc_info') as mock_report:
            with self.assertRaises(RuntimeError):
                run(testapp({'type': 'websocket'}, None, None))

            mock_report.assert_not_called()

    def test_should_support_type_hints(self):
        from rollbar.contrib.asgi.types import Receive, Scope, Send

        self.assertDictEqual(
            rollbar.contrib.asgi.ReporterMiddleware.__call__.__annotations__,
            {'scope': Scope, 'receive': Receive, 'send': Send, 'return': None},
        )
