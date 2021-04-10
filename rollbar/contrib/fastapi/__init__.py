from fastapi import __version__

import rollbar
from rollbar.contrib.asgi import ASGIMiddleware


class FastAPIMiddleware(ASGIMiddleware):
    ...


def _hook(request, data):
    data["framework"] = f"fastapi {__version__}"


rollbar.BASE_DATA_HOOK = _hook
