__all__ = ['ReporterMiddleware', 'add_to', 'LoggerMiddleware', 'get_current_request']

from fastapi import __version__

import rollbar
from .middleware import ReporterMiddleware
from .logger import LoggerMiddleware
from .routing import add_to

# Do not modify the returned request object
from rollbar.contrib.starlette import get_current_request


def _hook(request, data):
    data['framework'] = f'fastapi {__version__}'


rollbar.BASE_DATA_HOOK = _hook
