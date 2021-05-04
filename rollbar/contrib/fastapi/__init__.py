__all__ = ['add_to', 'ReporterMiddleware', 'get_current_request']

import sys

from fastapi import __version__

import rollbar
from .middleware import ReporterMiddleware
from .routing import add_to

if sys.version_info >= (3, 7):
    from .logger import LoggerMiddleware

    __all__.append('LoggerMiddleware')

# Do not modify the returned request object
from rollbar.contrib.starlette import get_current_request


def _hook(request, data):
    data['framework'] = f'fastapi {__version__}'


rollbar.BASE_DATA_HOOK = _hook
