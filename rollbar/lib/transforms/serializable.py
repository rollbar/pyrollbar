import base64

from rollbar.lib import do_for_python_version, iteritems, text, string_types, python_major_version
from rollbar.lib.transforms import Transform


class SerializableTransform(Transform):
    def __init__(self, whitelist_types=None):
        super(SerializableTransform, self).__init__()
        self.whitelist = set(whitelist_types or [])

    def _unencodable_object_message(self, data):
        return '<Unencodable type:(%s) base64:(%s)>' % (type(data).__name__,
                                                        base64.b64encode(data).decode('ascii'))

    def _undecodable_object_message(self, data):
        return '<Undecodable type:(%s) base64:(%s)>' % (type(data).__name__,
                                                        base64.b64encode(data).decode('ascii'))

    def transform_circular_reference(self, o, key=None, ref_key=None):
        if isinstance(o, self._allowed_circular_reference_types):
            # NOTE(cory): hack to perform the correct UTF8 checks for serialization of
            # circular references.
            if isinstance(o, string_types):
                return do_for_python_version(self.transform_py2_str,
                                             self.transform_unicode,
                                             o,
                                             key=key)

            return self.default(o, key=key)

        ref = '.'.join(map(text, ref_key or []))
        return '<Circular reference type:(%s) ref:(%s)>' % (type(o).__name__, ref)

    def transform_namedtuple(self, o, key=None):
        tuple_dict = o._asdict()
        transformed_dict = self.transform_dict(tuple_dict, key=key)
        new_vals = []
        for field in tuple_dict:
            new_vals.append(transformed_dict[field])

        return '<%s>' % text(o._make(new_vals))

    def transform_py2_str(self, o, key=None):
        try:
            o.decode('utf8')
        except UnicodeDecodeError:
            return self._undecodable_object_message(o)
        else:
            return o

    def transform_py3_bytes(self, o, key=None):
        return repr(o)

    def transform_unicode(self, o, key=None):
        try:
            o.encode('utf8')
        except UnicodeEncodeError:
            return self._unencodable_object_message(o)
        else:
            return o

    def transform_dict(self, o, key=None):
        ret = {}
        for k, v in iteritems(o):
            if isinstance(k, string_types):
                if python_major_version() < 3:
                    if isinstance(k, unicode):
                        new_k = self.transform_unicode(k)
                    else:
                        new_k = self.transform_py2_str(k)
                else:
                    if isinstance(k, bytes):
                        new_k = self.transform_py3_bytes(k)
                    else:
                        new_k = self.transform_unicode(k)
            else:
                new_k = text(k)

            ret[new_k] = v

        return super(SerializableTransform, self).transform_dict(ret, key=key)


    def transform_custom(self, o, key=None):
        if o is None:
            return None

        if any(filter(lambda x: isinstance(o, x), self.whitelist)):
            try:
                return repr(o)
            except TypeError:
                pass

        return str(type(o))


__all__ = ['SerializableTransform']
