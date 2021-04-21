__all__ = ['FastAPIMiddleware']

from rollbar.contrib.starlette import StarletteMiddleware


class FastAPIMiddleware(StarletteMiddleware):
    ...
