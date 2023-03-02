try:
    # Python 3
    from collections.abc import Iterable
except ImportError:
    # Python 2.7
    from collections import Iterable

from rollbar.lib import (
    python_major_version,
    binary_type,
    string_types,
    integer_types,
    number_types,
    traverse,
    walk,
    type_info,
)
from rollbar.lib.transform import Transform
from rollbar.lib.transforms.batched import BatchedTransform

_ALLOWED_CIRCULAR_REFERENCE_TYPES = [binary_type, bool, type(None)]

if isinstance(string_types, tuple):
    _ALLOWED_CIRCULAR_REFERENCE_TYPES.extend(string_types)
else:
    _ALLOWED_CIRCULAR_REFERENCE_TYPES.append(string_types)

if isinstance(number_types, tuple):
    _ALLOWED_CIRCULAR_REFERENCE_TYPES.extend(number_types)
else:
    _ALLOWED_CIRCULAR_REFERENCE_TYPES.append(number_types)

_ALLOWED_CIRCULAR_REFERENCE_TYPES = tuple(_ALLOWED_CIRCULAR_REFERENCE_TYPES)


def transform(obj, transforms, key=None, batch_transforms=False, batcher=None):
    if isinstance(transforms, Transform):
        transforms = [transforms]

    # if batcher:
    #     transforms = [batcher(transforms)]

    if batch_transforms:
        transforms = [BatchedTransform(transforms)]
    #     return _batched_transform(obj, transforms, key=key)

    for transform in transforms:
        obj = _transform(obj, transform, key=key)

    return obj


def _transform(obj, transform, key=None):
    key = key or ()

    def do_transform(type_name, val, key=None, **kw):
        fn = getattr(transform, "transform_%s" % type_name, transform.transform_custom)
        val = fn(val, key=key, **kw)

        return val

    if python_major_version() < 3:

        def string_handler(s, key=None):
            if isinstance(s, str):
                return do_transform("py2_str", s, key=key)
            elif isinstance(s, unicode):
                return do_transform("unicode", s, key=key)

    else:

        def string_handler(s, key=None):
            if isinstance(s, bytes):
                return do_transform("py3_bytes", s, key=key)
            elif isinstance(s, str):
                return do_transform("unicode", s, key=key)

    def default_handler(o, key=None):
        if isinstance(o, bool):
            return do_transform("boolean", o, key=key)

        # There is a quirk in the current version (1.1.6) of the enum
        # backport enum34 which causes it to not have the same
        # behavior as Python 3.4+. One way to identify IntEnums is that
        # they are instances of numbers but not number types.
        if isinstance(o, number_types):
            if type(o) not in number_types:
                return do_transform("custom", o, key=key)
            else:
                return do_transform("number", o, key=key)

        return do_transform("custom", o, key=key)

    handlers = {
        "string_handler": string_handler,
        "tuple_handler": lambda o, key=None: do_transform("tuple", o, key=key),
        "namedtuple_handler": lambda o, key=None: do_transform(
            "namedtuple", o, key=key
        ),
        "list_handler": lambda o, key=None: do_transform("list", o, key=key),
        "set_handler": lambda o, key=None: do_transform("set", o, key=key),
        "mapping_handler": lambda o, key=None: do_transform("dict", o, key=key),
        "circular_reference_handler": lambda o, key=None, ref_key=None: do_transform(
            "circular_reference", o, key=key, ref_key=ref_key
        ),
        "default_handler": default_handler,
        "allowed_circular_reference_types": _ALLOWED_CIRCULAR_REFERENCE_TYPES,
    }

    return traverse.traverse(obj, key=key, **handlers)


def safeset(source, path, val):
    if len(path) == 0:
        return source
    print(source, path)
    memo = source
    ancestors, dest = path[: len(path) - 1], path[len(path) - 1]
    for key in ancestors:
        try:
            memo = memo[key]
        except KeyError:
            return None
    if memo[dest]:
        memo[dest] = val
    return source


def _batched_transform(obj, transforms, key=None):
    key = key or ()

    def do_transform(transform, type_name, val, key=None, **kw):
        fn = getattr(transform, "transform_%s" % type_name, transform.transform_custom)
        val = fn(val, key=key, **kw)

        return val

    if python_major_version() < 3:

        def string_handler(transform, s, key=None):
            if isinstance(s, str):
                return do_transform(transform, "py2_str", s, key=key)
            elif isinstance(s, unicode):
                return do_transform(transform, "unicode", s, key=key)

    else:

        def string_handler(s, key=None):
            if isinstance(s, bytes):
                return do_transform(transform, "py3_bytes", s, key=key)
            elif isinstance(s, str):
                return do_transform(transform, "unicode", s, key=key)

    def default_handler(transform, o, key=None):
        if isinstance(o, bool):
            return do_transform(transform, "boolean", o, key=key)

        # There is a quirk in the current version (1.1.6) of the enum
        # backport enum34 which causes it to not have the same
        # behavior as Python 3.4+. One way to identify IntEnums is that
        # they are instances of numbers but not number types.
        if isinstance(o, number_types):
            if type(o) not in number_types:
                return do_transform(transform, "custom", o, key=key)
            else:
                return do_transform(transform, "number", o, key=key)

        return do_transform(transform, "custom", o, key=key)

    handlers = {
        type_info.STRING: string_handler,
        type_info.TUPLE: lambda transform, o, key=None: do_transform(
            transform, "tuple", o, key=key
        ),
        type_info.NAMEDTUPLE: lambda transform, o, key=None: do_transform(
            transform, "namedtuple", o, key=key
        ),
        type_info.LIST: lambda transform, o, key=None: do_transform(
            transform, "list", o, key=key
        ),
        type_info.SET: lambda transform, o, key=None: do_transform(
            transform, "set", o, key=key
        ),
        type_info.MAPPING: lambda transform, o, key=None: do_transform(
            transform, "dict", o, key=key
        ),
        type_info.CIRCULAR: lambda transform, o, key=None, ref_key=None: do_transform(
            transform, "circular_reference", o, key=key, ref_key=ref_key
        ),
        type_info.DEFAULT: default_handler,
    }

    for (node, k) in walk.walk(obj, key=key):
        for transform in transforms:
            node_type = type_info.get_type(node)
            handler = handlers.get(node_type, type_info.DEFAULT)
            handler(transform, node, k)

        safeset(obj, key, node)

    return obj


__all__ = ["transform", "Transform"]
