__all__ = ['FastAPIMiddleware', 'add_to']

from fastapi import __version__

import rollbar
from rollbar.contrib.fastapi.middleware import FastAPIMiddleware
from rollbar.contrib.fastapi.route import add_to


def _hook(request, data):
    data['framework'] = f'fastapi {__version__}'


rollbar.BASE_DATA_HOOK = _hook
