__all__ = ['FastAPIMiddleware', 'add_to', 'get_current_request']

from fastapi import __version__

import rollbar
from rollbar.contrib.fastapi.middleware import FastAPIMiddleware
from rollbar.contrib.fastapi.routing import add_to

# Do not modify returned request object
from rollbar.contrib.starlette import get_current_request


def _hook(request, data):
    data['framework'] = f'fastapi {__version__}'


rollbar.BASE_DATA_HOOK = _hook
