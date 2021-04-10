from starlette import __version__
from starlette.types import ASGIApp

import rollbar
from rollbar.contrib.asgi import ASGIMiddleware


class StarletteMiddleware(ASGIMiddleware):
    ...


def _hook(request, data):
    data["framework"] = f"starlette {__version__}"


rollbar.BASE_DATA_HOOK = _hook

