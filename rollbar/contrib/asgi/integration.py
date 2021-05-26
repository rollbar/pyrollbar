import inspect
import functools

import rollbar


class IntegrationBase:
    """
    Superclass for class integrations.
    """

    def __init__(self):
        if hasattr(self, '_integrate'):
            self._integrate()


class integrate:
    """
    Integrates functions and classes (derived from IntegrationBase) in the SDK.
    """

    def __init__(self, *, framework_name='unknown'):
        self._framework_name = framework_name

    def __call__(self, obj):
        if inspect.isclass(obj):
            obj._integrate = self._register_hook
            return obj
        else:
            return self._insert_hook(obj)

    def _register_hook(self):
        def _hook(request, data):
            data['framework'] = self._framework_name

        rollbar.BASE_DATA_HOOK = _hook

    def _insert_hook(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self._register_hook()
            return func(*args, **kwargs)

        return wrapper
