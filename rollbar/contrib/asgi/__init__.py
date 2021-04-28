__all__ = ['ASGIMiddleware']

import rollbar

from .middleware import ASGIMiddleware


def _hook(request, data):
    data['framework'] = 'asgi'


rollbar.BASE_DATA_HOOK = _hook
