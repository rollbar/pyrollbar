import logging

try:
    # Python 3
    from collections.abc import Mapping
    from collections.abc import Sequence
    from collections.abc import Set
except ImportError:
    # Python 2.7
    from collections import Mapping
    from collections import Sequence
    from collections import Set

from rollbar.lib import binary_type, iteritems, string_types, circular_reference_label

CIRCULAR = -1
DEFAULT = 0
MAPPING = 1
TUPLE = 2
NAMEDTUPLE = 3
LIST = 4
SET = 5
STRING = 6

log = logging.getLogger(__name__)


def _noop_circular(a, **kw):
    return circular_reference_label(a, ref_key=kw.get("ref_key"))


def _noop(a, **_):
    return a


def _noop_tuple(a, **_):
    return tuple(a)


def _noop_namedtuple(a, **_):
    return a._make(a)


def _noop_list(a, **_):
    return list(a)


def _noop_set(a, **_):
    return set(a)


def _noop_mapping(a, **_):
    return dict(a)


_default_handlers = {
    CIRCULAR: _noop_circular,
    DEFAULT: _noop,
    STRING: _noop,
    TUPLE: _noop_tuple,
    NAMEDTUPLE: _noop_namedtuple,
    LIST: _noop_list,
    SET: _noop_set,
    MAPPING: _noop_mapping,
}


def get_type(obj):
    if isinstance(obj, (string_types, binary_type)):
        return STRING

    if isinstance(obj, Mapping):
        return MAPPING

    if isinstance(obj, tuple):
        if hasattr(obj, "_fields"):
            return NAMEDTUPLE

        return TUPLE

    if isinstance(obj, set):
        return SET

    if isinstance(obj, Sequence):
        return LIST

    return DEFAULT


def walk(obj, handler, key=(), memo=None):
    key = key or ()

    if memo is None:
        memo = set()

    iterator = None

    if isinstance(obj, Mapping):
        print("a", obj)
        iterator = iteritems
    elif isinstance(obj, (Sequence, Set)) and not isinstance(obj, string_types):
        print("b", obj)
        iterator = enumerate
    else:
        print("c", obj)

    if iterator:
        if id(obj) not in memo:
            memo.add(id(obj))
            for key_component, value in iterator(obj):
                print("\n", value, obj)
                walk(value, handler=handler, key=key + (key_component,), memo=memo)
            memo.remove(id(obj))

    handler(obj, key=key)


__all__ = ["walk"]
