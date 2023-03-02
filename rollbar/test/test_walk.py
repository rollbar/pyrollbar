from rollbar.lib.walk import walk

from rollbar.test import BaseTest


class RollbarWalkTest(BaseTest):
    def assertWalk(self, input, want):
        # steps = []

        got = walk(
            input,
            # lambda o, key=None: steps.append((o, key)),
        )

        self.assertEqual(
            want,
            list(got),
        )

    def test_number(self):
        self.assertWalk(
            1,
            [(1, ())],
        )

    def test_flat_list(self):
        input = [0, 1, 2, 3]

        self.assertWalk(
            input,
            [
                (0, (0,)),
                (1, (1,)),
                (2, (2,)),
                (3, (3,)),
                (input, ()),
            ],
        )

    def test_flat_tuple(self):
        input = (0, 1, 2, 3)

        self.assertWalk(
            input,
            [
                (0, (0,)),
                (1, (1,)),
                (2, (2,)),
                (3, (3,)),
                (input, ()),
            ],
        )

    def test_nested(self):
        input = (0, [1, 2], {"a": 3, "b": (4, 5)})

        self.assertWalk(
            input,
            [
                (0, (0,)),
                (1, (1, 0)),
                (2, (1, 1)),
                (input[1], (1,)),
                (3, (2, "a")),
                (4, (2, "b", 0)),
                (5, (2, "b", 1)),
                (input[2].get("b"), (2, "b")),
                (input[2], (2,)),
                (input, ()),
            ],
        )

    def test_namedtuple(self):
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

        tup = NamedTuple((1, 2, 3), labels=["one", "two", "three"])

        self.assertWalk(tup, [(1, (0,)), (2, (1,)), (3, (2,)), ((1, 2, 3), ())])

        setattr(tup, "_fields", "not quite a named tuple")
        self.assertWalk(tup, [(1, (0,)), (2, (1,)), (3, (2,)), ((1, 2, 3), ())])
