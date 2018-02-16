import re

from rollbar.lib import events, filters

from rollbar.test import BaseTest


class CustomFiltersTest(BaseTest):
    def setUp(self):
        events.reset()
        filters.add_builtin_filters({})

    def test_ignore_by_setting_rollbar_ignore(self):
        class NotIgnoredByDefault(Exception):
            pass

        def _ignore_if_cruel_world_filter(exc_info, **kw):
            cls, exc, trace = exc_info
            if 'cruel world' in str(exc):
                exc._rollbar_ignore = True

            return exc_info

        events.add_exception_info_handler(_ignore_if_cruel_world_filter, pos=0)

        self.assertIsNot(events.on_exception_info((None, NotIgnoredByDefault('hello world'), None)), False)
        self.assertFalse(events.on_exception_info((None, NotIgnoredByDefault('hello cruel world'), None)))

    def test_ignore_messages_by_regex(self):
        regex = re.compile(r'cruel')

        def _ignore_cruel_world_substring(message, **kw):
            if regex.search(message):
                return False

            return message

        events.add_message_handler(_ignore_cruel_world_substring)

        self.assertFalse(events.on_message('hello cruel world'))
        self.assertIsNot(events.on_message('hello world'), False)

    def test_modify_payload(self):
        def _add_test_key(payload, **kw):
            payload['test'] = 333
            return payload

        events.add_payload_handler(_add_test_key)

        self.assertEqual(events.on_payload({'hello': 'world'}), {'hello': 'world', 'test': 333})
