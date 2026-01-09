from __future__ import annotations

__all__ = ['get_current_request']

import logging
import sys
from typing import Optional, Union

from starlette.requests import Request
from starlette.types import Receive, Scope

log = logging.getLogger(__name__)

_current_request: ContextVar[Request | None] = ContextVar(
        'rollbar-request-object', default=None
    )


def get_current_request() -> Optional[Request]:
    """
    Return current request.

    Do NOT modify the returned request object.
    """

    return _current_request.get()


def store_current_request(
    request_or_scope: Union[Request, Scope], receive: Optional[Receive] = None
) -> Optional[Request]:

    if receive is None:
        request = request_or_scope
    elif request_or_scope['type'] == 'http':
        request = Request(request_or_scope, receive)
    else:
        request = None

    _current_request.set(request)
    return request


def hasuser(request: Request) -> bool:
    try:
        return hasattr(request, 'user')
    except AssertionError:
        return False
