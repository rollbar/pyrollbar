import asyncio
import threading
import unittest

from rollbar.test import BaseTest
from rollbar.lib import session


class SessionTest(BaseTest):
    def test_session_threading(self):
        results = []

        def worker(headers):
            session.set_current_session(headers)
            results.append(session.get_current_session())

        t1 = threading.Thread(target=worker, args=({
            'Baggage': 'rollbar.session.id=abc123,rollbar.execution.scope.id=123abc'
        },))
        t2 = threading.Thread(target=worker, args=({
            'Baggage': 'rollbar.session.id=def456,rollbar.execution.scope.id=456def'
        },))
        t3 = threading.Thread(target=worker, args=({},))

        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], [
            {'key': 'session_id', 'value': 'abc123'},
            {'key': 'execution_scope_id', 'value': '123abc'},
        ])
        self.assertEqual(results[1], [
            {'key': 'session_id', 'value': 'def456'},
            {'key': 'execution_scope_id', 'value': '456def'},
        ])
        # For the thread with empty headers, we should still get a session ID generated.
        self.assertEqual(results[2][0]['key'], 'execution_scope_id')
        self.assertEqual(len(results[2][0]['value']), 32)

    def test_parse_session_request_baggage_headers(self):
        headers = {
            'Baggage': 'rollbar.session.id=abc123, rollbar.execution.scope.id=def456',
        }
        attributes = session.parse_session_request_baggage_headers(headers)
        self.assertEqual([
            {'key': 'session_id', 'value': 'abc123'},
            {'key': 'execution_scope_id', 'value': 'def456'},
        ], attributes)

    def test_parse_session_request_baggage_headers_lower(self):
        headers = {
            'baggage': 'rollbar.execution.scope.id=abc123',
        }
        attributes = session.parse_session_request_baggage_headers(headers)
        self.assertEqual([
            {'key': 'execution_scope_id', 'value': 'abc123'},
        ], attributes)

    def test_parse_session_request_baggage_headers_scope_only(self):
        headers = {
            'baggage': 'rollbar.execution.scope.id=def456',
        }
        attributes = session.parse_session_request_baggage_headers(headers)
        self.assertEqual([
            {'key': 'execution_scope_id', 'value': 'def456'},
        ], attributes)

    def test_parse_session_request_baggage_headers_empty(self):
        headers = {
            'baggage': '',
        }
        attributes = session.parse_session_request_baggage_headers(headers)
        self.assertEqual(len(attributes), 0)

    def test_parse_session_request_baggage_headers_empty_generate(self):
        headers = {
            'baggage': '',
        }
        attributes = session.parse_session_request_baggage_headers(headers, generate_missing=True)
        # Ensure that we still generate an execution scope ID if the baggage header is empty.
        self.assertEqual(len(attributes), 1)
        self.assertEqual(attributes[0]['key'], 'execution_scope_id')
        self.assertEqual(len(attributes[0]['value']), 32)

    def test_parse_session_request_baggage_headers_other(self):
        headers = {
            'baggage': 'some.id=xyz789',
        }
        attributes = session.parse_session_request_baggage_headers(headers)
        self.assertEqual(len(attributes), 0)

    def test_parse_session_request_baggage_headers_other_generate(self):
        headers = {
            'baggage': 'some.id=xyz789',
        }
        attributes = session.parse_session_request_baggage_headers(headers, generate_missing=True)
        # Ensure that we still generate an execution scope ID if the baggage header doesn't contain the expected keys.
        self.assertEqual(len(attributes), 1)
        self.assertEqual(attributes[0]['key'], 'execution_scope_id')
        self.assertEqual(len(attributes[0]['value']), 32)

    def test_build_new_session_attributes(self):
        attributes = session._build_new_scope_attributes()
        self.assertEqual(len(attributes), 1)
        self.assertEqual(attributes[0]['key'], 'execution_scope_id')
        self.assertEqual(len(attributes[0]['value']), 32)

    def test_new_session_id(self):
        session_id = session._new_scope_id()
        self.assertEqual(len(session_id), 32)


class TestSessionAsync(unittest.IsolatedAsyncioTestCase):
    """
    Test that session data is properly isolated across async tasks.
    """

    async def test_session_async(self):
        results = {}

        async def worker(headers, key):
            session.set_current_session(headers)
            await asyncio.sleep(0.1) # Force a context switch to test async isolation
            results[key] = session.get_current_session()

        await asyncio.gather(
            worker({'Baggage': 'rollbar.session.id=abc123,rollbar.execution.scope.id=123abc'}, 'task1'),
            worker({'Baggage': 'rollbar.session.id=def456,rollbar.execution.scope.id=456def'}, 'task2'),
            worker({}, 'task3'),
        )

        self.assertEqual(results['task1'], [
            {'key': 'session_id', 'value': 'abc123'},
            {'key': 'execution_scope_id', 'value': '123abc'},
        ])
        self.assertEqual(results['task2'], [
            {'key': 'session_id', 'value': 'def456'},
            {'key': 'execution_scope_id', 'value': '456def'},
        ])
        # For the task with empty headers, we should still get a session ID generated.
        self.assertEqual(results['task3'][0]['key'], 'execution_scope_id')
        self.assertEqual(len(results['task3'][0]['value']), 32)
