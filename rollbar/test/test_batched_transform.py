from rollbar.lib.transforms import transform
from rollbar.lib.transform import Transform
from rollbar.lib.traverse import traverse

from rollbar.test import BaseTest


class TrackingTransformer(Transform):
    def __init__(self):
        self.got = []

    def default(self, o, key=None):
        self.got.append((o, key))
        return o


class BatchedTransformTest(BaseTest):
    def assertTrackingTransform(self, input):
        tracking_transformer = TrackingTransformer()

        transforms = [
            tracking_transformer,
            tracking_transformer,
        ]

        transform(input, transforms, batch_transforms=True)

        want = []

        def dup_watch_handler(o, key=None):
            want.append((o, key))
            want.append((o, key))
            return o

        traverse(
            input,
            string_handler=dup_watch_handler,
            tuple_handler=dup_watch_handler,
            namedtuple_handler=dup_watch_handler,
            list_handler=dup_watch_handler,
            set_handler=dup_watch_handler,
            mapping_handler=dup_watch_handler,
            default_handler=dup_watch_handler,
            circular_reference_handler=dup_watch_handler,
        )

        self.assertEqual(want, tracking_transformer.got)

    def test_number(self):
        self.assertTrackingTransform(1)

    def test_flat_list(self):
        self.assertTrackingTransform([0, 1, 2, 3])

    def test_flat_tuple(self):
        self.assertTrackingTransform((0, 1, 2, 3))

    def test_nested_object(self):
        self.assertTrackingTransform((0, [1, 2], {"a": 3, "b": (4, 5)}))
