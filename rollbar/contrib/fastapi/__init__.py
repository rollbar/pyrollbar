import rollbar
from rollbar.contrib.asgi import ASGIMiddleware


class FastAPIMiddleware(ASGIMiddleware):
    ...


def _hook(request, data):
    data["framework"] = "fastapi"


rollbar.BASE_DATA_HOOK = _hook
