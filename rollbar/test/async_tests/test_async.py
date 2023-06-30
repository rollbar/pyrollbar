import copy
import sys

from unittest import mock

import unittest

import rollbar
from rollbar.lib._async import AsyncMock
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest.skipUnless(ALLOWED_PYTHON_VERSION, 'Async support requires Python3.6+')
class AsyncLibTest(BaseTest):
    default_settings = copy.deepcopy(rollbar.SETTINGS)

    def setUp(self):
        self.access_token = 'aaaabbbbccccddddeeeeffff00001111'
        rollbar.SETTINGS = copy.deepcopy(self.default_settings)
        rollbar._initialized = False
        rollbar.init(self.access_token, handler='async')

    @mock.patch('rollbar.send_payload')
    def test_report_exception(self, send_payload):
        from rollbar.lib._async import report_exc_info, run

        def _raise():
            try:
                raise Exception('foo')
            except:
                return run(report_exc_info())

        uuid = _raise()

        send_payload.assert_called_once()

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['data']['uuid'], uuid)
        self.assertEqual(payload['access_token'], self.access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('trace', payload['data']['body'])
        self.assertNotIn('trace_chain', payload['data']['body'])
        self.assertIn('exception', payload['data']['body']['trace'])
        self.assertEqual(
            payload['data']['body']['trace']['exception']['message'], 'foo'
        )
        self.assertEqual(
            payload['data']['body']['trace']['exception']['class'], 'Exception'
        )

        self.assertNotIn('argspec', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('varargspec', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('keywordspec', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('locals', payload['data']['body']['trace']['frames'][-1])

    @mock.patch('rollbar.send_payload')
    def test_report_messsage(self, send_payload):
        from rollbar.lib._async import report_message, run

        uuid = run(report_message('foo'))

        send_payload.assert_called_once()

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['data']['uuid'], uuid)
        self.assertEqual(payload['access_token'], self.access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('message', payload['data']['body'])
        self.assertIn('body', payload['data']['body']['message'])
        self.assertEqual(payload['data']['body']['message']['body'], 'foo')

    @mock.patch('rollbar.report_exc_info')
    def test_should_run_rollbar_report_exc_info(self, rollbar_report_exc_info):
        from rollbar.lib._async import report_exc_info, run

        try:
            raise Exception()
        except Exception:
            run(
                report_exc_info(
                    'exc_info',
                    'request',
                    'extra_data',
                    'payload_data',
                    'level_data',
                    foo='bar',
                )
            )

        rollbar_report_exc_info.assert_called_once_with(
            'exc_info', 'request', 'extra_data', 'payload_data', 'level_data', foo='bar'
        )

    @mock.patch('rollbar.report_message')
    def test_should_run_rollbar_report_message(self, rollbar_report_message):
        from rollbar.lib._async import report_message, run

        run(report_message('message', 'level', 'request', 'extra_data', 'payload_data'))

        rollbar_report_message.assert_called_once_with(
            'message', 'level', 'request', 'extra_data', 'payload_data'
        )

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_async')
    def test_report_exc_info_should_use_async_handler_regardless_of_settings(
        self, mock__send_payload_async, mock_log
    ):
        import rollbar
        from rollbar.lib._async import report_exc_info, run

        rollbar.SETTINGS['handler'] = 'thread'
        self.assertEqual(rollbar.SETTINGS['handler'], 'thread')

        run(report_exc_info())

        self.assertEqual(rollbar.SETTINGS['handler'], 'thread')
        mock__send_payload_async.assert_called_once()
        mock_log.assert_called_once_with(
            'Running coroutines requires async compatible handler. Switching to default async handler.'
        )

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_async')
    def test_report_message_should_use_async_handler_regardless_of_settings(
        self, mock__send_payload_async, mock_log
    ):
        import rollbar
        from rollbar.lib._async import report_message, run

        rollbar.SETTINGS['handler'] = 'thread'
        self.assertEqual(rollbar.SETTINGS['handler'], 'thread')

        run(report_message('foo'))

        self.assertEqual(rollbar.SETTINGS['handler'], 'thread')
        mock__send_payload_async.assert_called_once()
        mock_log.assert_called_once_with(
            'Running coroutines requires async compatible handler. Switching to default async handler.'
        )

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_async')
    def test_report_exc_info_should_allow_async_handler(
        self, mock__send_payload_async, mock_log
    ):
        import rollbar
        from rollbar.lib._async import report_exc_info, run

        rollbar.SETTINGS['handler'] = 'async'
        self.assertEqual(rollbar.SETTINGS['handler'], 'async')

        run(report_exc_info())

        self.assertEqual(rollbar.SETTINGS['handler'], 'async')
        mock__send_payload_async.assert_called_once()
        mock_log.assert_not_called()

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_async')
    def test_report_message_should_allow_async_handler(
        self, mock__send_payload_async, mock_log
    ):
        import rollbar
        from rollbar.lib._async import report_message, run

        rollbar.SETTINGS['handler'] = 'async'
        self.assertEqual(rollbar.SETTINGS['handler'], 'async')

        run(report_message('foo'))

        self.assertEqual(rollbar.SETTINGS['handler'], 'async')
        mock__send_payload_async.assert_called_once()
        mock_log.assert_not_called()

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_httpx')
    def test_report_exc_info_should_allow_httpx_handler(
        self, mock__send_payload_httpx, mock_log
    ):
        import rollbar
        from rollbar.lib._async import report_exc_info, run

        rollbar.SETTINGS['handler'] = 'httpx'
        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')

        run(report_exc_info())

        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')
        mock__send_payload_httpx.assert_called_once()
        mock_log.assert_not_called()

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_httpx')
    def test_report_message_should_allow_httpx_handler(
        self, mock__send_payload_httpx, mock_log
    ):
        import rollbar
        from rollbar.lib._async import report_message, run

        rollbar.SETTINGS['handler'] = 'httpx'
        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')

        run(report_message('foo', 'error'))

        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')
        mock__send_payload_httpx.assert_called_once()
        mock_log.assert_not_called()

    @mock.patch('logging.Logger.warning')
    def test_ctx_manager_should_use_async_handler(self, mock_log):
        import rollbar
        from rollbar.lib._async import AsyncHandler

        rollbar.SETTINGS['handler'] = 'thread'
        with AsyncHandler() as handler:
            self.assertEqual(handler, 'async')
            mock_log.assert_called_once_with(
                'Running coroutines requires async compatible handler.'
                ' Switching to default async handler.'
            )
        rollbar.SETTINGS['handler'] = 'thread'

    @mock.patch('logging.Logger.warning')
    def test_ctx_manager_should_use_global_handler_if_contextvar_is_not_supported(
        self, mock_log
    ):
        import rollbar
        import rollbar.lib._async
        from rollbar.lib._async import AsyncHandler

        try:
            # simulate missing `contextvars` module
            _ctx_handler = rollbar.lib._async._ctx_handler
            rollbar.lib._async._ctx_handler = None

            rollbar.SETTINGS['handler'] = 'thread'
            self.assertEqual(rollbar.SETTINGS['handler'], 'thread')

            with AsyncHandler() as handler:
                self.assertEqual(handler, 'thread')
                mock_log.assert_not_called()

            self.assertEqual(rollbar.SETTINGS['handler'], 'thread')
        finally:
            # restore original _ctx_handler
            rollbar.lib._async._ctx_handler = _ctx_handler

    @mock.patch('logging.Logger.warning')
    def test_ctx_manager_should_not_substitute_global_handler(self, mock_log):
        import rollbar
        from rollbar.lib._async import AsyncHandler

        rollbar.SETTINGS['handler'] = 'thread'
        self.assertEqual(rollbar.SETTINGS['handler'], 'thread')

        with AsyncHandler() as handler:
            self.assertEqual(handler, 'async')
            self.assertEqual(rollbar.SETTINGS['handler'], 'thread')

        self.assertEqual(rollbar.SETTINGS['handler'], 'thread')
        mock_log.assert_called_once_with(
            'Running coroutines requires async compatible handler.'
            ' Switching to default async handler.'
        )

    @mock.patch('rollbar._send_payload_httpx')
    @mock.patch('rollbar._send_payload_async')
    def test_report_exc_info_message_should_allow_multiple_async_handlers(
        self, mock__send_payload_async, mock__send_payload_httpx
    ):
        import asyncio
        import rollbar
        from rollbar.lib._async import report_exc_info, run

        async def report(handler):
            rollbar.SETTINGS['handler'] = handler
            try:
                raise Exception('foo')
            except:
                await report_exc_info()

        async def send_reports():
            await asyncio.gather(report('async'), report('httpx'))

        run(send_reports())

        mock__send_payload_async.assert_called_once()
        mock__send_payload_httpx.assert_called_once()

    @mock.patch('rollbar._send_payload_httpx')
    @mock.patch('rollbar._send_payload_async')
    def test_report_message_should_allow_multiple_async_handlers(
        self, mock__send_payload_async, mock__send_payload_httpx
    ):
        import asyncio
        import rollbar
        from rollbar.lib._async import report_message, run

        async def report(handler):
            rollbar.SETTINGS['handler'] = handler
            await report_message('foo')

        async def send_reports():
            await asyncio.gather(report('async'), report('httpx'))

        run(send_reports())

        mock__send_payload_async.assert_called_once()
        mock__send_payload_httpx.assert_called_once()

    @mock.patch('rollbar._send_payload')
    @mock.patch('rollbar._send_payload_thread')
    @mock.patch('rollbar._send_payload_httpx')
    @mock.patch('rollbar._send_payload_async')
    def test_report_exc_info_should_allow_multiple_handlers(
        self,
        mock__send_payload_async,
        mock__send_payload_httpx,
        mock__send_payload_thread,
        mock__send_payload,
    ):
        import asyncio
        import rollbar
        from rollbar.lib._async import report_exc_info, run

        async def async_report(handler):
            rollbar.SETTINGS['handler'] = handler
            try:
                raise Exception('foo')
            except:
                await report_exc_info()

        async def sync_report(handler):
            rollbar.SETTINGS['handler'] = handler
            try:
                raise Exception('foo')
            except:
                rollbar.report_exc_info()

        async def send_reports():
            await asyncio.gather(
                sync_report('thread'),
                async_report('httpx'),
                sync_report('blocking'),
                async_report('async'),
            )

        run(send_reports())

        mock__send_payload_async.assert_called_once()
        mock__send_payload_httpx.assert_called_once()
        mock__send_payload_thread.assert_called_once()
        mock__send_payload.assert_called_once()

    @mock.patch('rollbar._send_payload')
    @mock.patch('rollbar._send_payload_thread')
    @mock.patch('rollbar._send_payload_httpx')
    @mock.patch('rollbar._send_payload_async')
    def test_report_message_should_allow_multiple_handlers(
        self,
        mock__send_payload_async,
        mock__send_payload_httpx,
        mock__send_payload_thread,
        mock__send_payload,
    ):
        import asyncio
        import rollbar
        from rollbar.lib._async import report_message, run

        async def async_report(handler):
            rollbar.SETTINGS['handler'] = handler
            await report_message('foo')

        async def sync_report(handler):
            rollbar.SETTINGS['handler'] = handler
            rollbar.report_message('foo')

        async def send_reports():
            await asyncio.gather(
                sync_report('thread'),
                async_report('httpx'),
                sync_report('blocking'),
                async_report('async'),
            )

        run(send_reports())

        mock__send_payload_async.assert_called_once()
        mock__send_payload_httpx.assert_called_once()
        mock__send_payload_thread.assert_called_once()
        mock__send_payload.assert_called_once()

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_thread')
    @mock.patch('rollbar._send_payload_async')
    def test_report_exc_info_should_allow_multiple_handlers_with_threads(
        self,
        mock__send_payload_async,
        mock__send_payload_thread,
        mock_log,
    ):
        import time
        import threading
        import rollbar
        from rollbar.lib._async import report_exc_info, run

        async def async_report():
            try:
                raise Exception('foo')
            except:
                await report_exc_info()

        def sync_report():
            # give a chance to execute async_report() first
            time.sleep(0.1)

            try:
                raise Exception('foo')
            except:
                rollbar.report_exc_info()

        rollbar.SETTINGS['handler'] = 'thread'
        t1 = threading.Thread(target=run, args=(async_report(),))
        t2 = threading.Thread(target=sync_report)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        mock__send_payload_async.assert_called_once()
        mock__send_payload_thread.assert_called_once()
        mock_log.assert_called_once_with(
            'Running coroutines requires async compatible handler. Switching to default async handler.'
        )

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_thread')
    @mock.patch('rollbar._send_payload_async')
    def test_report_message_should_allow_multiple_handlers_with_threads(
        self,
        mock__send_payload_async,
        mock__send_payload_thread,
        mock_log,
    ):
        import time
        import threading
        import rollbar
        from rollbar.lib._async import report_message, run

        async def async_report():
            await report_message('foo')

        def sync_report():
            # give a chance to execute async_report() first
            time.sleep(0.1)
            rollbar.report_message('foo')

        rollbar.SETTINGS['handler'] = 'thread'
        t1 = threading.Thread(target=run, args=(async_report(),))
        t2 = threading.Thread(target=sync_report)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        mock__send_payload_async.assert_called_once()
        mock__send_payload_thread.assert_called_once()
        mock_log.assert_called_once_with(
            'Running coroutines requires async compatible handler. Switching to default async handler.'
        )

    @mock.patch('rollbar.lib._async.report_exc_info', new_callable=AsyncMock)
    def test_should_try_report_with_async_handler(self, async_report_exc_info):
        import rollbar
        from rollbar.lib._async import run, try_report

        rollbar.SETTINGS['handler'] = 'async'
        self.assertEqual(rollbar.SETTINGS['handler'], 'async')

        run(try_report())

        async_report_exc_info.assert_called_once()

    @mock.patch('rollbar.lib._async.report_exc_info', new_callable=AsyncMock)
    def test_should_try_report_if_default_handler(self, async_report_exc_info):
        import rollbar
        from rollbar.lib._async import run, try_report

        rollbar.SETTINGS['handler'] = 'default'
        self.assertEqual(rollbar.SETTINGS['handler'], 'default')

        run(try_report())

        async_report_exc_info.assert_called_once()

    @mock.patch('rollbar.lib._async.report_exc_info', new_callable=AsyncMock)
    def test_should_not_try_report_with_async_handler_if_non_async_handler(
        self, async_report_exc_info
    ):
        import rollbar
        from rollbar.lib._async import RollbarAsyncError, run, try_report

        rollbar.SETTINGS['handler'] = 'thread'
        self.assertEqual(rollbar.SETTINGS['handler'], 'thread')

        with self.assertRaises(RollbarAsyncError):
            run(try_report())

        async_report_exc_info.assert_not_called()

    @mock.patch('rollbar.lib._async.httpx', None)
    def test_try_report_should_raise_exc_if_httpx_package_is_missing(self):
        import rollbar
        from rollbar.lib._async import RollbarAsyncError, run, try_report

        rollbar.SETTINGS['handler'] = 'httpx'
        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')

        with self.assertRaises(RollbarAsyncError):
            run(try_report())

    @mock.patch('asyncio.ensure_future')
    def test_should_schedule_task_in_event_loop(self, ensure_future):
        from rollbar.lib._async import call_later, coroutine

        try:
            if sys.version_info >= (3, 7):
                with mock.patch('asyncio.create_task') as create_task:
                    coro = coroutine()
                    call_later(coro)

                    create_task.assert_called_once_with(coro)
                    ensure_future.assert_not_called()
            else:
                coro = coroutine()
                call_later(coro)

                ensure_future.assert_called_once_with(coro)
        finally:
            # make sure the coroutine is closed to avoid RuntimeWarning by calling
            # coroutine without awaiting it later
            coro.close()
