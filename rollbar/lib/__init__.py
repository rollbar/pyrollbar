import os
import sys

import six
from six.moves import urllib

iteritems = six.iteritems
reprlib = six.moves.reprlib

integer_types = six.integer_types
string_types = six.string_types

urlparse = urllib.parse.urlparse
urlsplit = urllib.parse.urlsplit
urlunparse = urllib.parse.urlunparse
urlunsplit = urllib.parse.urlunsplit
parse_qs = urllib.parse.parse_qs
urlencode = urllib.parse.urlencode
urljoin = urllib.parse.urljoin
quote = urllib.parse.quote


_version = sys.version_info


def python_major_version():
    return _version[0]


if python_major_version() <= 2:
    def text(val):
        if isinstance(val, (str, unicode)):
            return val

        conversion_options = [unicode, lambda x: unicode(x, encoding='utf8')]
        for option in conversion_options:
            try:
                return option(val)
            except UnicodeDecodeError:
                pass

        return repr(val)
else:
    def text(val):
        return str(val)


def do_for_python_version(two_fn, three_fn, *args, **kw):
    if python_major_version() < 3:
        return two_fn(*args, **kw)
    return three_fn(*args, **kw)


def prefix_match(key, prefixes):
    if not key:
        return False

    for prefix in prefixes:
        common_prefix = os.path.commonprefix((prefix, key))
        if common_prefix == prefix:
            return True

    return False


def key_in(key, keys):
    if not key:
        return False

    for k in keys:
        if key_match(k, key):
            return True

    return False


def key_match(key1, key2):
    key1_len = len(key1)
    key2_len = len(key2)
    if key1_len != key2_len:
        return False

    z_key = zip(key1, key2)
    num_matches = 0
    for p1, p2 in z_key:
        if '*' in (p1, p2) or p1 == p2:
            num_matches += 1

    return num_matches == key1_len


def reverse_list_of_lists(l, apply_each_fn=None):
    apply_each_fn = apply_each_fn or (lambda x: x)
    return map(lambda x: list(reversed(map(apply_each_fn, x))), l or [])


def build_key_matcher(prefixes_or_suffixes, type='prefix', case_sensitive=False):
    _prefixes = []

    if type == 'prefix':
        _iter = iter
    elif type == 'suffix':
        _iter = reversed
    else:
        raise ValueError('type must be either "prefix" or "suffix"')

    prefixes_or_suffixes = prefixes_or_suffixes or []
    for prefix in prefixes_or_suffixes:
        if case_sensitive:
            # Copy the list of lists
            _prefix = list(_iter(prefix))
        else:
            # Lowercase all of the elements
            _prefix = [x.lower() for x in _iter(prefix)]

        _prefixes.append(_prefix)

    def matcher(prefix_or_suffix):
        if case_sensitive:
            prefix = list(_iter(prefix_or_suffix))
        else:
            prefix = map(lambda x: str(x).lower(), _iter(prefix_or_suffix))

        return prefix_match(prefix, _prefixes)

    return matcher


def is_builtin_type(obj):
    return obj.__class__.__module__ in ('__builtin__', 'builtins')