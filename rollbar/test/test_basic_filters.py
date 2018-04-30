from rollbar.lib import events, filters

from rollbar.test import BaseTest


class BasicFiltersTest(BaseTest):
    def setUp(self):
        events.reset()
        filters.add_builtin_filters({})

    def test_rollbar_ignored_exception(self):
        class IgnoredException(Exception):
            _rollbar_ignore = True

        class NotIgnoredException(Exception):
            _rollbar_ignore = False

        self.assertFalse(events.on_exception_info((None, IgnoredException(), None)))
        self.assertIsNot(events.on_exception_info((None, NotIgnoredException(), None)), False)

    def test_filter_by_level(self):
        self.assertFalse(events.on_exception_info((None, 123, None), level='ignored'))
        self.assertIsNot(events.on_exception_info((None, 123, None), level='error'), False)

        self.assertFalse(events.on_message('hello world', level='ignored'))
        self.assertIsNot(events.on_message('hello world', level='error'), False)

        self.assertFalse(events.on_payload({}, level='ignored'))
        self.assertIsNot(events.on_message({}, level='error'), False)
