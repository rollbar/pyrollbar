__all__ = ['StarletteMiddleware']

from starlette import __version__

import rollbar
from rollbar.contrib.starlette.middleware import StarletteMiddleware


def _hook(request, data):
    data['framework'] = f'starlette {__version__}'


rollbar.BASE_DATA_HOOK = _hook
