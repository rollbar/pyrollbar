__all__ = ['StarletteMiddleware', 'get_current_request']

from starlette import __version__

import rollbar
from rollbar.contrib.starlette.middleware import StarletteMiddleware

# Do not modify returned request object
from rollbar.contrib.starlette.requests import get_current_request


def _hook(request, data):
    data['framework'] = f'starlette {__version__}'


rollbar.BASE_DATA_HOOK = _hook
