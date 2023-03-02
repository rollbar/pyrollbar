from rollbar.lib.transforms import _depth_first_transform as transform, Transform
from rollbar.lib.walk import walk

from rollbar.test import BaseTest


class TrackingTransformer(Transform):
    def __init__(self):
        self.seen = []

    def default(self, o, key=None):
        self.seen.append((o, key))
        return o


class RollbarTransformTest(BaseTest):
    def assertTrackingTransform(self, input):
        tracking_transformer = TrackingTransformer()

        transforms = [
            tracking_transformer,
            tracking_transformer,
        ]

        transform(input, transforms)

        want = []

        for (node, key) in walk(input):
            want.append((node, key))
            want.append((node, key))

        self.assertEqual(want, tracking_transformer.seen)

    def test_number(self):
        self.assertTrackingTransform(1)

    def test_flat_list(self):
        self.assertTrackingTransform([0, 1, 2, 3])

    def test_flat_tuple(self):
        self.assertTrackingTransform((0, 1, 2, 3))

    def test_nested_object(self):
        self.assertTrackingTransform((0, [1, 2], {"a": 3, "b": (4, 5)}))
