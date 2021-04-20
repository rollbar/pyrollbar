__all__ = ['FastAPIMiddleware']

from fastapi import __version__

import rollbar
from rollbar.contrib.starlette import StarletteMiddleware


class FastAPIMiddleware(StarletteMiddleware):
    ...


def _hook(request, data):
    data['framework'] = f'fastapi {__version__}'


rollbar.BASE_DATA_HOOK = _hook
