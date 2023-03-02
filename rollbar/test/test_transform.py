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
    def setUp(self):
        self.tracking_transformer = TrackingTransformer()

        self.transforms = [
            self.tracking_transformer,
            self.tracking_transformer,
        ]

    def assertTransform(self, input):
        want = []

        for (node, key) in walk(input):
            want.append((node, key))
            want.append((node, key))

        transform(input, self.transforms)

        self.assertEqual(want, self.tracking_transformer.seen)

    def test_number(self):
        self.assertTransform(1)

        # transform(
        #     1,
        #     self.transforms,
        # )
        #
        # self.assertEqual(
        #     [(1, ()), (1, ())],
        #     self.tracking_transformer.seen,
        # )

    def test_flat_list(self):
        self.assertTransform([0, 1, 2, 3])
        # input = [0, 1, 2, 3]

        # got = transform(
        #     input,
        #     self.transforms,
        # )
        #
        # self.assertEqual(input, got)
        #
        # self.assertEqual(
        #     [
        #         (0, (0,)),
        #         (0, (0,)),
        #         (1, (1,)),
        #         (1, (1,)),
        #         (2, (2,)),
        #         (2, (2,)),
        #         (3, (3,)),
        #         (3, (3,)),
        #         (input, ()),
        #         (input, ()),
        #     ],
        #     self.tracking_transformer.seen,
        # )

    def test_flat_tuple(self):
        self.assertTransform((0, 1, 2, 3))
        #
        # got = transform(
        #     input,
        #     self.transforms,
        # )
        #
        # self.assertEqual(input, got)
        #
        # self.assertEqual(
        #     [
        #         (0, (0,)),
        #         (0, (0,)),
        #         (1, (1,)),
        #         (1, (1,)),
        #         (2, (2,)),
        #         (2, (2,)),
        #         (3, (3,)),
        #         (3, (3,)),
        #         (input, ()),
        #         (input, ()),
        #     ],
        #     self.tracking_transformer.seen,
        # )

    def test_nested_object(self):
        self.assertTransform((0, [1, 2], {"a": 3, "b": (4, 5)}))

        # got = transform(
        #     input,
        #     self.transforms,
        # )
        #
        # self.assertEqual(
        #     [
        #         (0, (0,)),
        #         (0, (0,)),
        #         (1, (1, 0)),
        #         (1, (1, 0)),
        #         (2, (1, 1)),
        #         (2, (1, 1)),
        #         (input[1], (1,)),
        #         (input[1], (1,)),
        #         (input[2].get("a"), (2, "a")),
        #         (input[2].get("a"), (2, "a")),
        #         (4, (2, "b", 0)),
        #         (4, (2, "b", 0)),
        #         (5, (2, "b", 1)),
        #         (5, (2, "b", 1)),
        #         (input[2].get("b"), (2, "b")),
        #         (input[2].get("b"), (2, "b")),
        #         (input[2], (2,)),
        #         (input[2], (2,)),
        #         (input, ()),
        #         (input, ()),
        #     ],
        #     self.tracking_transformer.seen,
        # )
        #
        # self.assertEqual(
        #     input,
        #     got,
        # )
