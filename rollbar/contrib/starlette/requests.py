__all__ = ['get_current_request']

try:
    from contextvars import ContextVar
except ImportError:
    ContextVar = None
import logging
from typing import Optional, Union

from starlette.requests import Request
from starlette.types import Receive, Scope

log = logging.getLogger(__name__)

if ContextVar:
    _current_request: ContextVar[Request] = ContextVar('request', default=None)


def get_current_request() -> Optional[Request]:
    """
    Return current request.

    Do NOT modify the returned request object.
    """

    if ContextVar is None:
        log.error('Python 3.7+ is required to receive current request.')
        return None

    request = _current_request.get()

    if request is None:
        log.error('Request is not available in the present context.')
        return None

    return request


def store_current_request(
    request_or_scope: Union[Request, Scope], receive: Optional[Receive] = None
) -> Optional[Request]:
    if ContextVar is None:
        return None

    if receive is None:
        request = request_or_scope
    else:
        request = Request(request_or_scope, receive)

    _current_request.set(request)
    return request


def hasuser(request: Request) -> bool:
    try:
        return hasattr(request, 'user')
    except AssertionError:
        return False
