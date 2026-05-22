from __future__ import annotations

__all__ = ['get_current_request']

import logging
from typing import MutableMapping
from contextvars import ContextVar

from starlette.requests import Request
from starlette.types import Receive, Scope

log = logging.getLogger(__name__)

_current_request: ContextVar[Request | None] = ContextVar(
    'rollbar-request-object', default=None
)


def get_current_request() -> Request | None:
    """
    Return current request.

    Do NOT modify the returned request object.
    """

    return _current_request.get()


def store_current_request(request_or_scope: Request | Scope, receive: Receive | None = None) -> Request | None:
    """
    Store the current request in an async-safe context variable.
    """

    request: Request | None = None
    if isinstance(request_or_scope, Request):
        request = request_or_scope
    elif isinstance(request_or_scope, MutableMapping) and request_or_scope['type'] == 'http' and receive is not None:
        # The above condition checks if request_or_scope is a Scope
        request = Request(request_or_scope, receive)

    _current_request.set(request)
    return request


def hasuser(request: Request) -> bool:
    try:
        return hasattr(request, 'user')
    except AssertionError:
        return False
