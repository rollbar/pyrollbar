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

# dual python 2/3 compatability, inspired by the "six" library
string_types = (str, unicode) if str is bytes else (str, bytes)


def iteritems(mapping):
    return getattr(mapping, "iteritems", mapping.items)()


def walk(obj, path=(), memo=None):
    if memo is None:
        memo = set()
    iterator = None
    if isinstance(obj, Mapping):
        iterator = iteritems
    elif isinstance(obj, (Sequence, Set)) and not isinstance(obj, string_types):
        iterator = enumerate
    if iterator:
        if id(obj) not in memo:
            memo.add(id(obj))
            for path_component, value in iterator(obj):
                for result in walk(value, path + (path_component,), memo):
                    yield result
            memo.remove(id(obj))

    # else:
    yield path, obj
