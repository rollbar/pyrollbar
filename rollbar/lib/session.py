from __future__ import annotations

import random
import threading
from contextvars import ContextVar

from rollbar.lib.payload import Attribute

_context_session: ContextVar[list[Attribute]|None] = ContextVar('rollbar-session', default=None)
_thread_session: threading.local = threading.local()


def set_current_session(headers: dict[str, str]) -> None:
    """
    Set current session data.

    The session data should be a dictionary with string keys and string values.
    """
    session_data = _parse_session_request_baggage_headers(headers)
    _context_session.set(session_data)
    _thread_session.data = session_data


def get_current_session() -> list[Attribute]:
    """
    Return current session data.

    Do NOT modify the returned session data.
    """
    session_data = _context_session.get()
    if session_data is not None:
        return session_data

    # Fallback to thread local storage for non-async contexts.
    return getattr(_thread_session, 'data', None) or []


def reset_current_session() -> None:
    """
    Reset current session data.
    """
    _context_session.set(None)
    _thread_session.data = None


def _parse_session_request_baggage_headers(headers: dict) -> list[Attribute]:
    """
    Parse the 'baggage' header from the request headers to extract session information. If the 'baggage' header is not
    present or does not contain the expected keys, a new session ID will be generated and returned as part of the session attributes.
    """
    if not headers:
        return _build_new_session_attributes()

    baggage_header = None

    # Make sure to handle case-insensitive header keys.
    for key in headers.keys():
        if key.lower() == 'baggage':
            baggage_header = headers[key]
            break

    if not baggage_header:
        return _build_new_session_attributes()

    baggage_items = baggage_header.split(',')
    baggage_data = []
    for item in baggage_items:
        if '=' not in item:
            continue
        key, value = item.split('=', 1)
        key = key.strip()
        if key == 'rollbar.session.id':
            baggage_data.append({'key': 'session_id', 'value': value.strip()})
        if key == 'rollbar.execution.scope.id':
            baggage_data.append({'key': 'execution_scope_id', 'value': value.strip()})

    if not baggage_data:
        return _build_new_session_attributes()

    return baggage_data


def _build_new_session_attributes() -> list[Attribute]:
    new_id = _new_session_id()
    if new_id is None:
        return []
    return [{'key': 'session_id', 'value': new_id}]


def _new_session_id() -> str | None:
    try:
        # Generate a random integer with exactly 128 random bits
        num = random.getrandbits(128)
    except Exception as e:
        return None
    return format(num, "032x")
