from rollbar.lib.transforms import transform, Transform

from rollbar.test import BaseTest


# class Counter:
#     value = 1
#
#
# class IncrementingIncrementer(Transform):
#     def __init__(self, counter):
#         super().__init__()
#         self._counter = counter
#         self.calls = 0
#
#     def transform_number(self, o, key=None):
#         next = o + self._counter.value
#         self._counter.value += 1
#         self.calls += 1
#         return next
#
#
# class DoublingIncrementer(Transform):
#     def __init__(self, counter):
#         super().__init__()
#         self._counter = counter
#         self.calls = 0
#
#     def transform_number(self, o, key=None):
#         next = o + self._counter.value
#         self._counter.value *= 2
#         self.calls += 1
#         return next


class TrackingTransformer(Transform):
    def __init__(self):
        self.seen = []

    def default(self, o, key=None):
        self.seen.append((o, key))
        return o


class RollbarTransformTest(BaseTest):
    def setUp(self):
        # counter = Counter()

        self.tracking_transformer = TrackingTransformer()

        self.transforms = [
            self.tracking_transformer,
            self.tracking_transformer,
            # IncrementingIncrementer(counter),
            # DoublingIncrementer(counter),
        ]

    def test_number(self):
        transform(
            1,
            self.transforms,
        )

        self.assertEqual(
            [(1, ()), (1, ())],
            self.tracking_transformer.seen,
        )

    def test_flat_list(self):
        input = [0, 1, 2, 3]

        got = transform(
            input,
            self.transforms,
        )

        self.assertEqual(input, got)

        self.assertEqual(
            [
                (0, (0,)),
                (0, (0,)),
                (1, (1,)),
                (1, (1,)),
                (2, (2,)),
                (2, (2,)),
                (3, (3,)),
                (3, (3,)),
                (input, ()),
                (input, ()),
            ],
            self.tracking_transformer.seen,
        )

        # self.assertEqual(4, self.transforms[0].calls)
        # self.assertEqual(4, self.transforms[1].calls)
        # self.assertEqual(
        #     got,
        #     [2, 6, 42, 1806],
        # )

    def test_flat_tuple(self):
        input = (0, 1, 2, 3)

        got = transform(
            input,
            self.transforms,
        )

        self.assertEqual(input, got)

        self.assertEqual(
            [
                (0, (0,)),
                (0, (0,)),
                (1, (1,)),
                (1, (1,)),
                (2, (2,)),
                (2, (2,)),
                (3, (3,)),
                (3, (3,)),
                (input, ()),
                (input, ()),
            ],
            self.tracking_transformer.seen,
        )

        # self.assertEqual(
        #     transform(
        #         (0, 0, 0, 0),
        #         self.transforms,
        #     ),
        #     (2, 6, 42, 1806),
        # )

    def test_nested_object(self):
        input = (0, [1, 2], {"a": 3, "b": (4, 5)})

        got = transform(
            input,
            self.transforms,
        )

        self.assertEqual(
            [
                (0, (0,)),
                (0, (0,)),
                (1, (1, 0)),
                (1, (1, 0)),
                (2, (1, 1)),
                (2, (1, 1)),
                (input[1], (1,)),
                (input[1], (1,)),
                (3, (2, "a")),
                (3, (2, "a")),
                (4, (2, "b", 0)),
                (4, (2, "b", 0)),
                (5, (2, "b", 1)),
                (5, (2, "b", 1)),
                (input[2].get("b"), (1, "b")),
                (input[2].get("b"), (1, "b")),
                (input[1], (1,)),
                (input[1], (1,)),
                (input, ()),
                (input, ()),
            ],
            self.tracking_transformer.seen,
        )

        self.assertEqual(
            input,
            got,
        )
