__all__ = ['ReporterMiddleware']

import rollbar

from .middleware import ReporterMiddleware


def _hook(request, data):
    data['framework'] = 'asgi'


rollbar.BASE_DATA_HOOK = _hook
