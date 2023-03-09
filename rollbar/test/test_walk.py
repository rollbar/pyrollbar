from rollbar.lib.walk import walk

from rollbar.test import BaseTest


class WalkTest(BaseTest):
    def test_walk(self):
        cases = [
            (0, [((), 0)]),
            (
                (0, 1, 2, 3, 4, 5),
                [
                    ((0,), 0),
                    ((1,), 1),
                    ((2,), 2),
                    ((3,), 3),
                    ((4,), 4),
                    ((5,), 5),
                    ((), (0, 1, 2, 3, 4, 5)),
                ],
            ),
            (
                (0, [1, 2], {"a": 3, "b": (4, 5)}),
                [
                    ((0,), 0),
                    ((1, 0), 1),
                    (
                        (
                            1,
                            1,
                        ),
                        2,
                    ),
                    ((1,), [1, 2]),
                    ((2, "a"), 3),
                    ((2, "b", 0), 4),
                    ((2, "b", 1), 5),
                    ((2, "b"), (4, 5)),
                    ((2,), {"a": 3, "b": (4, 5)}),
                    (
                        (),
                        (0, [1, 2], {"a": 3, "b": (4, 5)}),
                    ),
                ],
            ),
        ]

        for (input, want) in cases:
            got = list(walk(input))
            self.assertEqual(got, want)

    def test_named_tuple(self):
        """
        Objects that appear to be a namedtuple, like SQLAlchemy's KeyedTuple,
        will cause an Exception while identifying them if they don't implement
        the _make method.
        """

        class NamedTuple(tuple):
            """
            Modeled after NamedTuple and KeyedTuple from SQLAlchemy 0.7 and 0.8.
            """

            def __new__(cls, vals, labels=None):
                t = tuple.__new__(cls, vals)
                if labels:
                    t.__dict__.update(zip(labels, vals))
                    t._labels = labels
                return t

            def keys(self):
                return [l for l in self._labels if l is not None]

        input = NamedTuple((1, 2, 3), labels=["one", "two", "three"])
        self.assertEqual(
            list(walk(input)), [((0,), 1), ((1,), 2), ((2,), 3), ((), (1, 2, 3))]
        )
        setattr(input, "_fields", "not quite a named tuple")
        self.assertEqual(
            list(walk(input)), [((0,), 1), ((1,), 2), ((2,), 3), ((), (1, 2, 3))]
        )
