__all__ = ['ReporterMiddleware', 'get_current_request']

import sys

from starlette import __version__

import rollbar
from .middleware import ReporterMiddleware

if sys.version_info >= (3, 7):
    from .logger import LoggerMiddleware

    __all__.append('LoggerMiddleware')

# Do not modify the returned request object
from .requests import get_current_request


def _hook(request, data):
    data['framework'] = f'starlette {__version__}'


rollbar.BASE_DATA_HOOK = _hook
