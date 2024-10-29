class Transform(object):
    depth_first = True

    def default(self, o, key=None):
        return o

    def transform_circular_reference(self, o, key=None, ref_key=None):
        # By default, we just perform a no-op for circular references.
        # Subclasses should implement this method to return whatever representation
        # for the circular reference they need.
        return self.default(o, key=key)

    def transform_tuple(self, o, key=None):
        return self.default(o, key=key)

    def transform_namedtuple(self, o, key=None):
        return self.default(o, key=key)

    def transform_list(self, o, key=None):
        return self.default(o, key=key)

    def transform_dict(self, o, key=None):
        return self.default(o, key=key)

    def transform_number(self, o, key=None):
        return self.default(o, key=key)

    def transform_bytes(self, o, key=None):
        return self.default(o, key=key)

    def transform_unicode(self, o, key=None):
        return self.default(o, key=key)

    def transform_boolean(self, o, key=None):
        return self.default(o, key=key)

    def transform_path(self, o, key=None):
        return self.default(str(o), key=key)

    def transform_custom(self, o, key=None):
        return self.default(o, key=key)
