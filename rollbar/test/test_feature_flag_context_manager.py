import copy

try:
    from unittest import mock
except ImportError:
    import mock

import rollbar

from rollbar.test import BaseTest


_test_access_token = 'aaaabbbbccccddddeeeeffff00001111'
_default_settings = copy.deepcopy(rollbar.SETTINGS)


class FeatureFlagContextManagerTest(BaseTest):
    def setUp(self):
        rollbar._initialized = False
        rollbar.SETTINGS = copy.deepcopy(_default_settings)
        rollbar.init(_test_access_token, locals={'enabled': True}, handler='blocking', timeout=12345)

    def test_feature_flag_generates_correct_tag_payload(self):
        cm = rollbar.feature_flag('feature-foo', variation=True, user='atran@rollbar.com')

        tags = cm.tag
        self.assertEqual(len(tags), 4)

        key, order, variation, user = tags

        self.assertEqual(key['key'], 'feature_flag.key')
        self.assertEqual(key['value'], 'feature-foo')

        self.assertEqual(order['key'], 'feature_flag.data.feature-foo.order')
        self.assertEqual(order['value'], 0)

        self.assertEqual(variation['key'], 'feature_flag.data.feature-foo.variation')
        self.assertEqual(variation['value'], True)

        self.assertEqual(user['key'], 'feature_flag.data.feature-foo.user')
        self.assertEqual(user['value'], 'atran@rollbar.com')

    @mock.patch('rollbar.send_payload')
    def test_report_message_inside_feature_flag_context_manager(self, send_payload):
        with rollbar.feature_flag('feature-foo'):
            rollbar.report_message('hello world')

        self.assertEqual(send_payload.called, True)

        # [0][0] is used here to index into the mocked objects `call_args` and get the
        # right payload for comparison.
        payload_data = send_payload.call_args[0][0]['data']
        self.assertIn('tags', payload_data)

        tags = payload_data['tags']
        self.assertEquals(len(tags), 2)

        self._assert_tag_equals(tags[0], 'feature_flag.key', 'feature-foo')
        self._assert_tag_equals(tags[1], 'feature_flag.data.feature-foo.order', 0)

        self._report_message_and_assert_no_tags(send_payload)

    @mock.patch('rollbar.send_payload')
    def test_report_exc_info_inside_feature_flag_context_manager(self, send_payload):
        with rollbar.feature_flag('feature-foo'):
            try:
                raise Exception('foo')
            except:
                rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload_data = send_payload.call_args[0][0]['data']
        self.assertIn('tags', payload_data)

        tags = payload_data['tags']
        self.assertEquals(len(tags), 2)

        self._assert_tag_equals(tags[0], 'feature_flag.key', 'feature-foo')
        self._assert_tag_equals(tags[1], 'feature_flag.data.feature-foo.order', 0)

        self._report_message_and_assert_no_tags(send_payload)

    @mock.patch('rollbar.send_payload')
    def test_report_exc_info_outside_feature_flag_context_manager(self, send_payload):
        try:
            with rollbar.feature_flag('feature-foo'):
                raise Exception('foo')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload_data = send_payload.call_args[0][0]['data']
        self.assertIn('tags', payload_data)

        tags = payload_data['tags']
        self.assertEquals(len(tags), 2)

        self._assert_tag_equals(tags[0], 'feature_flag.key', 'feature-foo')
        self._assert_tag_equals(tags[1], 'feature_flag.data.feature-foo.order', 0)

        self._report_message_and_assert_no_tags(send_payload)

    @mock.patch('rollbar.send_payload')
    def test_report_exc_info_inside_nested_feature_flag_context_manager(self, send_payload):
        try:
            with rollbar.feature_flag('feature-foo'):
                with rollbar.feature_flag('feature-bar'):
                    raise Exception('foo')
        except:
            rollbar.report_exc_info()

        self.assertEqual(send_payload.called, True)

        payload_data = send_payload.call_args[0][0]['data']
        self.assertIn('tags', payload_data)

        tags = payload_data['tags']
        self.assertEquals(len(tags), 4)

        self._assert_tag_equals(tags[0], 'feature_flag.key', 'feature-foo')
        self._assert_tag_equals(tags[1], 'feature_flag.data.feature-foo.order', 0)
        self._assert_tag_equals(tags[2], 'feature_flag.key', 'feature-bar')
        self._assert_tag_equals(tags[3], 'feature_flag.data.feature-bar.order', 1)

        self._report_message_and_assert_no_tags(send_payload)

    def _assert_tag_equals(self, tag, key, value):
        self.assertEqual(tag, {'key': key, 'value': value})

    def _report_message_and_assert_no_tags(self, mocked_send):
        rollbar.report_message('this report message is to check that there are no tags')
        self.assertEqual(mocked_send.called, True)

        payload_data = mocked_send.call_args[0][0]['data']
        self.assertNotIn('tags', payload_data)
