__all__ = ['get_current_request']

try:
    from contextvars import ContextVar
except ImportError:
    ContextVar = None
import logging
from typing import Optional

from starlette.requests import Request
from starlette.types import Receive, Scope

log = logging.getLogger(__name__)

if ContextVar:
    _current_request: ContextVar[Request] = ContextVar('request', default=None)


def get_current_request() -> Optional[Request]:
    """
    The request object is read-only.

    Do NOT modify the returned request object.
    """

    if ContextVar is None:
        log.error('To receive current request Python 3.7+ is required')
        return None

    request = _current_request.get()

    if request is None:
        log.error('No request available in the current context')

    return request


def store_current_request(scope: Scope, receive: Receive) -> Optional[Request]:
    if ContextVar is None:
        return None

    request = Request(scope, receive)
    _current_request.set(request)
    return request
