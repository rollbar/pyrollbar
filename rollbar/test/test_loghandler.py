"""
Tests for the RollbarHandler logging handler
"""
import copy
import json
import logging
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import rollbar
from rollbar.logger import RollbarHandler

from rollbar.test import BaseTest


_test_access_token = 'aaaabbbbccccddddeeeeffff00001111'
_test_environment = 'test'
_default_settings = copy.deepcopy(rollbar.SETTINGS)

class CauseException(Exception):
    pass


class LogHandlerTest(BaseTest):
    def setUp(self):
        rollbar._initialized = False
        rollbar.SETTINGS = copy.deepcopy(_default_settings)

    def _create_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        self.rollbar_handler = RollbarHandler(_test_access_token, _test_environment)
        self.rollbar_handler.setLevel(logging.WARNING)

        logger.addHandler(self.rollbar_handler)

        return logger

    @mock.patch('rollbar.send_payload')
    def test_message_gets_formatted(self, send_payload):
        logger = self._create_logger()
        logger.warning("Hello %d %s", 1, 'world')

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['data']['body']['message']['body'], "Hello 1 world")
        self.assertEqual(payload['data']['body']['message']['args'], (1, 'world'))
        self.assertEqual(payload['data']['body']['message']['record']['name'], __name__)

    @mock.patch('rollbar.send_payload')
    def test_string_or_int_level(self, send_payload):
        logger = self._create_logger()
        logger.setLevel(logging.ERROR)
        self.rollbar_handler.setLevel('WARNING')
        logger.error("I am an error")

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['data']['level'], 'error')

        self.rollbar_handler.setLevel(logging.WARNING)
        logger.error("I am an error")

        self.assertEqual(payload['data']['level'], 'error')

    def test_request_is_get_from_log_record_if_present(self):
        logger = self._create_logger()
        # Request objects vary depending on python frameworks or packages.
        # Using a dictionary for this test is enough.
        request = {"fake": "request", "for":  "testing purporse"}

        # No need to test request parsing and payload sent,
        # just need to be sure that proper rollbar function is called
        # with passed request as argument.
        with mock.patch("rollbar.report_message") as report_message_mock:
            logger.warning("Warning message", extra={"request": request})
            self.assertEqual(report_message_mock.call_args[1]["request"], request)

        # Python 2.6 doesnt support extra param in logger.exception.
        if not sys.version_info[:2] == (2, 6):
            # if you call logger.exception outside of an exception
            # handler, it shouldn't try to report exc_info, since it
            # won't have any
            with mock.patch("rollbar.report_exc_info") as report_exc_info:
                with mock.patch("rollbar.report_message") as report_message_mock:
                    logger.exception("Exception message", extra={"request": request})
                    report_exc_info.assert_not_called()
                    self.assertEqual(report_message_mock.call_args[1]["request"], request)

            with mock.patch("rollbar.report_exc_info") as report_exc_info:
                with mock.patch("rollbar.report_message") as report_message_mock:
                    try:
                        raise Exception()
                    except:
                        logger.exception("Exception message", extra={"request": request})
                        self.assertEqual(report_exc_info.call_args[1]["request"], request)
                        report_message_mock.assert_not_called()

    @mock.patch('rollbar.send_payload')
    def test_nested_exception_trace_chain(self, send_payload):
        logger = self._create_logger()

        def _raise_context():
            bar_local = 'bar'
            raise CauseException('bar')

        def _raise_ex():
            try:
                _raise_context()
            except CauseException as context:
                # python2 won't automatically assign this traceback...
                exc_info = sys.exc_info()
                setattr(context, '__traceback__', exc_info[2])
                try:
                    foo_local = 'foo'
                    # in python3 __context__ is automatically set when an exception is raised in an except block
                    e = Exception('foo')
                    setattr(e, '__context__', context)  # PEP-3134
                    raise e
                except:
                    logger.exception("Bad time")

        _raise_ex()

        self.assertEqual(send_payload.called, True)
        payload = send_payload.call_args[0][0]
        body = payload['data']['body']
        trace = body['trace'] if 'trace' in body else None
        trace_chain = body['trace_chain'] if 'trace_chain' in body else None
        has_only_trace_chain = trace is None and trace_chain is not None
        has_only_trace = trace is not None and trace_chain is None
        self.assertTrue(has_only_trace or has_only_trace_chain)
        if trace_chain is not None:
            self.assertEqual('Bad time', payload['data']['custom']['exception']['description'])
        if trace is not None:
            self.assertEqual('Bad time', trace['exception']['description'])

    @mock.patch('rollbar.send_payload')
    def test_not_nested_exception_trace_chain(self, send_payload):
        logger = self._create_logger()

        def _raise_context():
            bar_local = 'bar'
            raise CauseException('bar')

        def _raise_ex():
            try:
                _raise_context()
            except:
                logger.exception("Bad time")

        _raise_ex()

        self.assertEqual(send_payload.called, True)
        payload = send_payload.call_args[0][0]
        body = payload['data']['body']
        trace = body['trace'] if 'trace' in body else None
        trace_chain = body['trace_chain'] if 'trace_chain' in body else None
        has_only_trace_chain = trace is None and trace_chain is not None
        has_only_trace = trace is not None and trace_chain is None
        self.assertTrue(has_only_trace or has_only_trace_chain)
        if trace_chain is not None:
            self.assertEqual('Bad time', payload['data']['custom']['exception']['description'])
        if trace is not None:
            self.assertEqual('Bad time', trace['exception']['description'])
