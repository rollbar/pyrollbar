__all__ = ['StarletteMiddleware', 'LoggerMiddleware', 'get_current_request']

from starlette import __version__

import rollbar
from .middleware import StarletteMiddleware
from .logger import LoggerMiddleware

# Do not modify returned request object
from .requests import get_current_request


def _hook(request, data):
    data['framework'] = f'starlette {__version__}'


rollbar.BASE_DATA_HOOK = _hook
