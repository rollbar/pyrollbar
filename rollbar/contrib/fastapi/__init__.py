"""Integration with fastapi.

See: https://fastapi.tiangolo.com/
"""

import rollbar

from fastapi import Request


def report_exception(request: Request):
    rollbar.report_exc_info(request=request)


def _hook(request, data):
    data["framework"] = "fastapi"

    if request:
        endpoint = request.scope["endpoint"]
        data["context"] = f"{endpoint.__module__}.{endpoint.__name__}"


rollbar.BASE_DATA_HOOK = _hook
