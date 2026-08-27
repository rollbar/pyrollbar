from __future__ import annotations

import logging
import re
import typing
import weakref
from inspect import getattr_static

from requests.sessions import Session
from requests.structures import CaseInsensitiveDict

from rollbar.lib.session import get_propagation_header
from rollbar.lib.propagation import (
    HeaderValue,
    URLMatcher,
    baggage_is_enabled,
    has_rollbar_baggage,
    normalize_exact_url,
    replace_rollbar_baggage,
)
from rollbar.lib.wrap import wrap_callable, unwrap_callable

log = logging.getLogger(__name__)


class _InstrumentationState:
    def __init__(
            self,
            enabled_urls: list[str | re.Pattern[str]],
            enabled_headers: list[str],
    ) -> None:
        self.enabled_urls = enabled_urls
        self.enabled_headers = enabled_headers
        # Cache configuration work because this state is read for every request.
        self.baggage_enabled = baggage_is_enabled(enabled_headers)
        self.matcher = URLMatcher(enabled_urls)
        self.active = True


class InstrumentedSession(_InstrumentationState):
    def __init__(
            self,
            enabled_urls: list[str | re.Pattern[str]],
            enabled_headers: list[str],
            *,
            had_instance_send: bool,
            original_instance_send: typing.Any,
    ) -> None:
        super().__init__(enabled_urls, enabled_headers)
        self.had_instance_send = had_instance_send
        self.original_instance_send = original_instance_send
        self.wrapper_ref: weakref.ReferenceType[typing.Callable[..., typing.Any]] | None = None


class RequestsContextPropagationManager:
    """
    Propagate Rollbar baggage globally or for one requests session.
    """

    _globally_instrumented: typing.ClassVar[bool] = False
    _original_send: typing.ClassVar[typing.Callable[..., typing.Any] | None] = None
    _global_wrapper: typing.ClassVar[typing.Callable[..., typing.Any] | None] = None
    _global_state: typing.ClassVar[_InstrumentationState | None] = None
    _sessions: typing.ClassVar[
        weakref.WeakKeyDictionary[Session, InstrumentedSession]
    ] = weakref.WeakKeyDictionary()

    @staticmethod
    def _prepare_headers(
            headers: typing.Mapping[str, HeaderValue] | None,
    ) -> CaseInsensitiveDict[HeaderValue]:
        return CaseInsensitiveDict(headers or {})

    @staticmethod
    def _baggage_is_enabled(enabled_headers: list[str]) -> bool:
        return baggage_is_enabled(enabled_headers)

    @classmethod
    def _replace_rollbar_baggage(
            cls,
            headers: CaseInsensitiveDict[HeaderValue],
            propagation_header: str | None,
    ) -> None:
        replace_rollbar_baggage(headers, propagation_header)

    @classmethod
    def _inject_propagation_headers(
            cls,
            state: _InstrumentationState,
            args: tuple[typing.Any, ...],
            kwargs: dict[str, typing.Any],
    ) -> None:
        if not state.baggage_enabled:
            return

        request = args[0] if args else kwargs.get("request")
        if request is None or not hasattr(request, "headers"):
            return

        url = getattr(request, "url", None)
        url_is_enabled = state.matcher.matches(url)
        propagation_header = get_propagation_header() if url_is_enabled else None
        # Avoid copying headers when there is nothing to add or sanitize.
        if propagation_header is None and not has_rollbar_baggage(request.headers):
            return
        headers = cls._prepare_headers(request.headers)
        cls._replace_rollbar_baggage(headers, propagation_header)
        request.headers = headers

    @staticmethod
    def _normalize_exact_url(url: str) -> str:
        return normalize_exact_url(url)

    @classmethod
    def _request_url_is_enabled(
            cls,
            url: str | None,
            enabled_urls: list[str | re.Pattern[str]],
    ) -> bool:
        return URLMatcher(enabled_urls).matches(url)

    @staticmethod
    def _callable_chain_contains(
            current: typing.Any,
            target: typing.Callable[..., typing.Any] | None,
    ) -> bool:
        if target is None:
            return False

        seen: set[int] = set()
        while callable(current) and id(current) not in seen:
            if current is target:
                return True
            seen.add(id(current))
            current = getattr(current, "__wrapped__", None)
        return False

    @classmethod
    def _wrapper(
            cls,
            state: _InstrumentationState,
            *,
            global_wrapper: bool = False,
    ) -> typing.Callable[..., typing.Any]:
        def wrapper_func(
                wrapped: typing.Callable[..., typing.Any],
                *args: typing.Any,
                **kwargs: typing.Any,
        ) -> typing.Any:
            should_inject = state.active
            if global_wrapper:
                session = getattr(wrapped, "__self__", None)
                # A session's explicit configuration overrides the global one.
                should_inject = should_inject and session not in cls._sessions

            if should_inject:
                try:
                    cls._inject_propagation_headers(
                        state,
                        args,
                        kwargs,
                    )
                except Exception as e:
                    log.error("Error injecting Rollbar propagation headers into request: %s", e)
            return wrapped(*args, **kwargs)

        return wrapper_func

    @classmethod
    def instrument(
            cls,
            enabled_urls: list[str | re.Pattern[str]],
            enabled_headers: list[str],
    ) -> None:
        """
        Enable propagation of Rollbar baggage headers globally for requests.

        Requests releases without ``Session.send`` are left unmodified.

        :param enabled_urls: A list of URLs or regex patterns to enable propagation for.
        :param enabled_headers: A list of headers to enable propagation for. Defaults to ["baggage"].
        :return: None
        """
        if cls._globally_instrumented:
            return

        current_send = getattr(Session, "send", None)
        if not callable(current_send):
            return

        if (
                cls._global_state is not None
                and cls._callable_chain_contains(current_send, cls._global_wrapper)
        ):
            # A later wrapper may still contain our inactive wrapper; reuse it.
            cls._global_state.enabled_urls = enabled_urls
            cls._global_state.enabled_headers = enabled_headers
            cls._global_state.baggage_enabled = baggage_is_enabled(enabled_headers)
            cls._global_state.matcher = URLMatcher(enabled_urls)
            cls._global_state.active = True
            cls._globally_instrumented = True
            return

        state = _InstrumentationState(enabled_urls, enabled_headers)
        cls._original_send = current_send
        cls._global_state = state
        wrap_callable(
            Session,
            "send",
            cls._wrapper(state, global_wrapper=True),
        )
        cls._global_wrapper = getattr_static(Session, "send")
        cls._globally_instrumented = True

    @classmethod
    def uninstrument(cls) -> None:
        """
        Globally remove instrumentation from requests to stop propagating Rollbar baggage headers.

        Note: This will not uninstrument sessions that were instrumented individually with ``instrument_session()``. To
        uninstrument those sessions, you must call ``uninstrument_session()`` on each one individually.
        :return: None
        """
        if not cls._globally_instrumented:
            return

        if cls._global_state is not None:
            # Later wrappers may own Session.send, so disable before restoring.
            cls._global_state.active = False

        current_send = getattr_static(Session, "send")
        if current_send is cls._global_wrapper and cls._original_send is not None:
            unwrap_callable(Session, "send", cls._original_send)
            cls._original_send = None
            cls._global_wrapper = None
            cls._global_state = None
        elif not cls._callable_chain_contains(current_send, cls._global_wrapper):
            cls._original_send = None
            cls._global_wrapper = None
            cls._global_state = None

        cls._globally_instrumented = False

    @classmethod
    def instrument_session(
            cls,
            session: Session,
            enabled_urls: list[str | re.Pattern[str]],
            enabled_headers: list[str] | None = None,
    ) -> None:
        """
        Enable propagation for one session instance.

        Any session-level configuration takes precedence over global configuration for the instrumented session. If the
        session is already instrumented, calling this method will raise a ``ValueError``. Use ``uninstrument_session()``
        first to remove the existing instrumentation.

        :param session: The requests session to instrument.
        :param enabled_urls: A list of URLs or regex patterns to enable propagation for.
        :param enabled_headers: A list of headers to enable propagation for. Defaults to ["baggage"].
        :return: None
        """
        if enabled_headers is None:
            enabled_headers = ["baggage"]

        if session in cls._sessions:
            raise ValueError('Session already instrumented. Use uninstrument_session() first.')
        if not callable(getattr(session, "send", None)):
            raise RuntimeError("This requests version does not provide Session.send")

        had_instance_send = "send" in vars(session)
        original_instance_send = getattr_static(session, "send") if had_instance_send else None
        state = InstrumentedSession(
            enabled_urls,
            enabled_headers,
            had_instance_send=had_instance_send,
            original_instance_send=original_instance_send,
        )
        wrap_callable(session, "send", cls._wrapper(state))
        # A weak reference keeps the registry from retaining the session indirectly.
        state.wrapper_ref = weakref.ref(getattr_static(session, "send"))
        cls._sessions[session] = state
        setattr(session, "_rollbar_requests_context_propagation_instrumented", True)

    @classmethod
    def uninstrument_session(cls, session: Session) -> None:
        """
        Disable propagation for one session instance.

        Note: This will not disable global propagation if the session was instrumented globally. You must call
        ``uninstrument()`` in that case to disable global propagation.

        :param session: The requests session to remove instrumentation from.
        :return: None
        """
        state = cls._sessions.pop(session, None)
        if state is None:
            setattr(session, "_rollbar_requests_context_propagation_instrumented", False)
            return

        state.active = False
        current_send = vars(session).get("send")
        wrapper = state.wrapper_ref() if state.wrapper_ref is not None else None
        # Do not overwrite a wrapper installed after Rollbar's wrapper.
        if current_send is wrapper:
            if state.had_instance_send:
                setattr(session, "send", state.original_instance_send)
            else:
                delattr(session, "send")

        setattr(session, "_rollbar_requests_context_propagation_instrumented", False)
