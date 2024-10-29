from rollbar.lib.transform import Transform
from rollbar.lib.traverse import traverse

from rollbar.test import BaseTest


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


class KeyMemTransform(Transform):
    """
    A transform that just stores the keys.
    """
    keys = []

    def default(self, o, key=None):
        self.keys.append((key, o))
        return o


class RollbarTraverseTest(BaseTest):
    """
    Objects that appear to be a namedtuple, like SQLAlchemy's KeyedTuple,
    will cause an Exception while identifying them if they don't implement
    the _make method.
    """

    def setUp(self):
        self.tuple = NamedTuple((1, 2, 3), labels=["one", "two", "three"])

    def test_base_case(self):
        self.assertEqual(traverse(self.tuple), (1, 2, 3))

    def test_bad_object(self):
        setattr(self.tuple, "_fields", "not quite a named tuple")
        self.assertEqual(traverse(self.tuple), (1, 2, 3))

    def test_depth_first(self):
        obj = {
            "one": ["four", "five", 6, 7],
            "two": ("eight", "nine", "ten"),
            "three": {
                "eleven": 12,
                "thirteen": 14
            }
        }
        transform = KeyMemTransform()
        transform.keys = []

        traverse(
            obj,
            key=(),
            string_handler=transform.default,
            tuple_handler=transform.default,
            namedtuple_handler=transform.default,
            list_handler=transform.default,
            set_handler=transform.default,
            mapping_handler=transform.default,
            path_handler=transform.default,
            default_handler=transform.default,
            circular_reference_handler=transform.default,
            allowed_circular_reference_types=transform.default,
        )

        self.assertEqual(
            transform.keys,
            [
                (("one", 0), "four"),
                (("one", 1), "five"),
                (("one", 2), 6),
                (("one", 3), 7),
                (("one",), ["four", "five", 6, 7]),
                (("two", 0), "eight"),
                (("two", 1), "nine"),
                (("two", 2), "ten"),
                (("two",), ("eight", "nine", "ten")),
                (("three", "eleven"), 12),
                (("three", "thirteen"), 14),
                (("three",), {
                    "eleven": 12,
                    "thirteen": 14
                }),
                ((), {
                    "one": ["four", "five", 6, 7],
                    "two": ("eight", "nine", "ten"),
                    "three": {
                        "eleven": 12,
                        "thirteen": 14
                    }
                }),
            ],
        )

    def test_breadth_first(self):
        obj = {
            "one": ["four", "five", 6, 7],
            "two": ("eight", "nine", "ten"),
            "three": {
                "eleven": 12,
                "thirteen": 14
            }
        }
        transform = KeyMemTransform()
        transform.keys = []

        traverse(
            obj,
            key=(),
            string_handler=transform.default,
            tuple_handler=transform.default,
            namedtuple_handler=transform.default,
            list_handler=transform.default,
            set_handler=transform.default,
            mapping_handler=transform.default,
            path_handler=transform.default,
            default_handler=transform.default,
            circular_reference_handler=transform.default,
            allowed_circular_reference_types=transform.default,
            depth_first=False,
        )

        self.assertEqual(
            transform.keys,
            [
                ((), {
                    "one": ["four", "five", 6, 7],
                    "two": ("eight", "nine", "ten"),
                    "three": {
                        "eleven": 12,
                        "thirteen": 14
                    }
                }),
                (("one",), ["four", "five", 6, 7]),
                (("one", 0), "four"),
                (("one", 1), "five"),
                (("one", 2), 6),
                (("one", 3), 7),
                (("two",), ("eight", "nine", "ten")),
                (("two", 0), "eight"),
                (("two", 1), "nine"),
                (("two", 2), "ten"),
                (("three",), {
                    "eleven": 12,
                    "thirteen": 14
                }),
                (("three", "eleven"), 12),
                (("three", "thirteen"), 14),
            ],
        )
