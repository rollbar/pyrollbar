import copy

import rollbar
from rollbar.test import BaseTest
from rollbar.lib.transforms import Transform
from rollbar.lib.transforms.shortener import ShortenerTransform
from rollbar.lib.transforms.scrub_redact import ScrubRedactTransform
from rollbar.lib.transforms.serializable import SerializableTransform
from rollbar.lib.transforms.scrub import ScrubTransform
from rollbar.lib.transforms.scruburl import ScrubUrlTransform

_test_access_token = 'aaaabbbbccccddddeeeeffff00001111'
_default_settings = copy.deepcopy(rollbar.SETTINGS)


class TransformTest(BaseTest):
    def setUp(self):
        rollbar._initialized = False
        rollbar.SETTINGS = copy.deepcopy(_default_settings)
        rollbar.init(_test_access_token, locals={'enabled': True}, handler='blocking', timeout=12345)

    def test_default_transforms(self):
        transforms = {transform.__class__ for transform in rollbar._transforms}

        self.assertEqual({
            ShortenerTransform,
            ScrubRedactTransform,
            SerializableTransform,
            ScrubUrlTransform,
        }, transforms)

    def test_add_custom_transform(self):
        class CustomTransform(Transform):
            pass

        rollbar._initialized = False
        rollbar.SETTINGS = copy.deepcopy(_default_settings)
        rollbar.init(_test_access_token,
                     locals={'enabled': True},
                     handler='blocking',
                     timeout=12345,
                     custom_transforms=[CustomTransform()])

        transforms = {transform.__class__ for transform in rollbar._transforms}
        transforms_ordered = [transform.__class__ for transform in rollbar._transforms]

        self.assertEqual({
            ShortenerTransform,
            ScrubRedactTransform,
            SerializableTransform,
            ScrubUrlTransform,
            CustomTransform,
        }, transforms)

        # CustomTransform should be last because it has the default priority of 100
        self.assertEqual([
            ShortenerTransform,
            ScrubRedactTransform,
            SerializableTransform,
            ScrubUrlTransform,
            CustomTransform,
        ], transforms_ordered)

    def test_add_custom_transform_first(self):
        class CustomTransform(Transform):
            priority = 1

        class CustomTransformTwo(Transform):
            priority = 35

        rollbar._initialized = False
        rollbar.SETTINGS = copy.deepcopy(_default_settings)
        rollbar.init(_test_access_token,
                     locals={'enabled': True},
                     handler='blocking',
                     timeout=12345,
                     custom_transforms=[CustomTransform(), CustomTransformTwo()])

        transforms = [transform.__class__ for transform in rollbar._transforms]

        # Custom transforms should be first and fifth.
        self.assertEqual([
            CustomTransform,  # priority 1
            ShortenerTransform,  # priority 10
            ScrubRedactTransform,  # priority 20
            SerializableTransform,  # priority 30
            CustomTransformTwo,  # priority 35
            ScrubUrlTransform,  # priority 50
        ], transforms)
