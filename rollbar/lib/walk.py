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

from rollbar.lib import binary_type, iteritems, string_types, circular_reference_label, type_info


log = logging.getLogger(__name__)




def walk(value, key=(), memo=None):
    key = key or ()

    if memo is None:
        memo = set()

    iterator = None

    if isinstance(value, Mapping):
        iterator = iteritems
    elif isinstance(value, (Sequence, Set)) and not isinstance(value, string_types):
        iterator = enumerate

    if iterator:
        if id(value) not in memo:
            memo.add(id(value))
            for key_component, child in iterator(value):
                for v, k in walk(child, key=key + (key_component,), memo=memo):
                    yield v, k
            memo.remove(id(value))

    yield value, key


__all__ = ["walk"]
