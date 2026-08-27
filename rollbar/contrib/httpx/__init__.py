from __future__ import annotations

import logging
import re
import typing
import weakref
from inspect import getattr_static

import httpx

from rollbar.lib.propagation import (
    HeaderValue,
    URLMatcher,
    baggage_is_enabled,
    has_rollbar_baggage,
    normalize_exact_url,
    replace_rollbar_baggage,
)
from rollbar.lib.session import get_propagation_header
from rollbar.lib.wrap import wrap_callable, unwrap_callable

log = logging.getLogger(__name__)


class _InstrumentationState:
    def __init__(self, enabled_urls: list[str | re.Pattern[str]], enabled_headers: list[str]) -> None:
        self.enabled_urls = enabled_urls
        self.enabled_headers = enabled_headers
        # Cache configuration work because this state is read for every request.
        self.baggage_enabled = baggage_is_enabled(enabled_headers)
        self.matcher = URLMatcher(enabled_urls)
        self.active = True


class InstrumentedClient(_InstrumentationState):
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


class HTTPXContextPropagationManager:
    """
    Propagate Rollbar baggage globally or for one HTTPX client.
    """

    _globally_instrumented: typing.ClassVar[bool] = False
    _original_sync_send: typing.ClassVar[typing.Callable[..., typing.Any] | None] = None
    _original_async_send: typing.ClassVar[typing.Callable[..., typing.Any] | None] = None
    _global_sync_wrapper: typing.ClassVar[typing.Callable[..., typing.Any] | None] = None
    _global_async_wrapper: typing.ClassVar[typing.Callable[..., typing.Any] | None] = None
    _global_state: typing.ClassVar[_InstrumentationState | None] = None
    _clients: typing.ClassVar[
        weakref.WeakKeyDictionary[httpx.Client | httpx.AsyncClient, InstrumentedClient]
    ] = weakref.WeakKeyDictionary()

    @staticmethod
    def _prepare_headers(headers: httpx.Headers | None) -> httpx.Headers:
        return httpx.Headers(headers)

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
        allowed = state.matcher.matches(getattr(request, "url", None))
        propagation_header = get_propagation_header() if allowed else None
        # Avoid copying headers when there is nothing to add or sanitize.
        if propagation_header is None and not has_rollbar_baggage(request.headers):
            return
        headers = cls._prepare_headers(request.headers)
        replace_rollbar_baggage(
            typing.cast(typing.MutableMapping[str, HeaderValue], headers),
            propagation_header,
        )
        request.headers = headers

    @staticmethod
    def _normalize_exact_url(url: str) -> str:
        return normalize_exact_url(url)

    @staticmethod
    def _request_url_is_enabled(
            url: str | httpx.URL,
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
    def _sync_wrapper(
            cls, state: _InstrumentationState, *, global_wrapper: bool = False,
    ) -> typing.Callable[..., typing.Any]:
        def wrapper_func(
                wrapped: typing.Callable[..., typing.Any],
                *args: typing.Any,
                **kwargs: typing.Any,
        ) -> typing.Any:
            should_inject = state.active
            if global_wrapper:
                client = getattr(wrapped, "__self__", None)
                # A client's explicit configuration overrides the global one.
                should_inject = should_inject and client not in cls._clients
            if should_inject:
                try:
                    cls._inject_propagation_headers(state, args, kwargs)
                except Exception as e:
                    log.error("Error injecting Rollbar propagation headers into request: %s", e)
            return wrapped(*args, **kwargs)
        return wrapper_func

    @classmethod
    def _async_wrapper(
            cls, state: _InstrumentationState, *, global_wrapper: bool = False,
    ) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
        async def wrapper_func(
                wrapped: typing.Callable[..., typing.Awaitable[typing.Any]],
                *args: typing.Any,
                **kwargs: typing.Any,
        ) -> typing.Any:
            should_inject = state.active
            if global_wrapper:
                client = getattr(wrapped, "__self__", None)
                # A client's explicit configuration overrides the global one.
                should_inject = should_inject and client not in cls._clients
            if should_inject:
                try:
                    cls._inject_propagation_headers(state, args, kwargs)
                except Exception as e:
                    log.error("Error injecting Rollbar propagation headers into request: %s", e)
            return await wrapped(*args, **kwargs)
        return wrapper_func

    @classmethod
    def instrument(
            cls,
            enabled_urls: list[str | re.Pattern[str]],
            enabled_headers: list[str],
    ) -> None:
        """
        Enable propagation of Rollbar baggage headers globally for HTTPX.

        :param enabled_urls: A list of URLs or regex patterns to enable propagation for.
        :param enabled_headers: A list of headers to enable propagation for. Defaults to ["baggage"].
        :return: None
        """
        if cls._globally_instrumented:
            return
        # This method runs once per redirect hop and works with custom transports.
        sync_send = getattr(httpx.Client, "_send_single_request", None)
        async_send = getattr(httpx.AsyncClient, "_send_single_request", None)
        if not callable(sync_send) and not callable(async_send):
            return
        sync_contains = cls._callable_chain_contains(sync_send, cls._global_sync_wrapper)
        async_contains = cls._callable_chain_contains(async_send, cls._global_async_wrapper)
        # A later wrapper may still contain our inactive wrapper; reuse it safely.
        if cls._global_state is not None and (sync_contains or async_contains):
            cls._global_state.enabled_urls = enabled_urls
            cls._global_state.enabled_headers = enabled_headers
            cls._global_state.baggage_enabled = baggage_is_enabled(enabled_headers)
            cls._global_state.matcher = URLMatcher(enabled_urls)
            cls._global_state.active = True
            if callable(sync_send) and not sync_contains:
                cls._original_sync_send = sync_send
                wrap_callable(
                    httpx.Client,
                    "_send_single_request",
                    cls._sync_wrapper(cls._global_state, global_wrapper=True),
                )
                cls._global_sync_wrapper = getattr_static(httpx.Client, "_send_single_request")
            if callable(async_send) and not async_contains:
                cls._original_async_send = async_send
                wrap_callable(
                    httpx.AsyncClient,
                    "_send_single_request",
                    cls._async_wrapper(cls._global_state, global_wrapper=True),
                )
                cls._global_async_wrapper = getattr_static(httpx.AsyncClient, "_send_single_request")
            cls._globally_instrumented = True
            return

        state = _InstrumentationState(enabled_urls, enabled_headers)
        cls._global_state = state
        if callable(sync_send):
            cls._original_sync_send = sync_send
            wrap_callable(httpx.Client, "_send_single_request", cls._sync_wrapper(state, global_wrapper=True))
            cls._global_sync_wrapper = getattr_static(httpx.Client, "_send_single_request")
        if callable(async_send):
            cls._original_async_send = async_send
            wrap_callable(httpx.AsyncClient, "_send_single_request", cls._async_wrapper(state, global_wrapper=True))
            cls._global_async_wrapper = getattr_static(httpx.AsyncClient, "_send_single_request")
        cls._globally_instrumented = True

    @classmethod
    def uninstrument(cls) -> None:
        """
        Globally remove instrumentation from HTTPX to stop propagating Rollbar baggage headers.

        Note: This will not uninstrument clients that were instrumented individually with ``instrument_client()``. To
        uninstrument those clients, you must call ``uninstrument_client()`` on each one individually.
        :return: None
        """
        if not cls._globally_instrumented:
            return
        if cls._global_state is not None:
            # Later wrappers may own the public attribute, so disable first.
            cls._global_state.active = False
        cls._restore_global_method(httpx.Client, cls._global_sync_wrapper, cls._original_sync_send)
        cls._restore_global_method(httpx.AsyncClient, cls._global_async_wrapper, cls._original_async_send)

        sync_current = getattr_static(httpx.Client, "_send_single_request", None)
        async_current = getattr_static(httpx.AsyncClient, "_send_single_request", None)
        sync_remains = cls._callable_chain_contains(sync_current, cls._global_sync_wrapper)
        async_remains = cls._callable_chain_contains(async_current, cls._global_async_wrapper)
        if not sync_remains:
            cls._original_sync_send = None
            cls._global_sync_wrapper = None
        if not async_remains:
            cls._original_async_send = None
            cls._global_async_wrapper = None
        if not sync_remains and not async_remains:
            cls._global_state = None
        cls._globally_instrumented = False

    @staticmethod
    def _restore_global_method(
            owner: type[typing.Any],
            wrapper: typing.Callable[..., typing.Any] | None,
            original: typing.Callable[..., typing.Any] | None,
    ) -> None:
        if wrapper is not None and original is not None:
            # Restore only when Rollbar still owns the outermost wrapper.
            if getattr_static(owner, "_send_single_request", None) is wrapper:
                unwrap_callable(owner, "_send_single_request", original)

    @classmethod
    def instrument_client(
            cls,
            client: httpx.Client | httpx.AsyncClient,
            enabled_urls: list[str | re.Pattern[str]],
            enabled_headers: list[str] | None = None,
    ) -> None:
        """
        Instrument a single HTTPX client to propagate Rollbar baggage headers.

        Any client that has been instrumented will take precedence over global configuration. If a client is already
        instrumented, this method will raise a ``ValueError``. To reconfigure an instrumented client, call
        ``uninstrument_client()`` first.

        :param client: The HTTPX client to instrument.
        :param enabled_urls: A list of URLs or regex patterns to enable propagation for.
        :param enabled_headers: A list of headers to enable propagation for. Defaults to ["baggage"] if not provided.
        :return: None
        """
        if enabled_headers is None:
            enabled_headers = ["baggage"]
        if client in cls._clients:
            raise ValueError("Client already instrumented. Use uninstrument_client() first.")
        if not callable(getattr(client, "_send_single_request", None)):
            raise RuntimeError("This HTTPX version does not provide _send_single_request")

        had_instance_send = "_send_single_request" in vars(client)
        original_instance_send = getattr_static(client, "_send_single_request") if had_instance_send else None
        state = InstrumentedClient(
            enabled_urls,
            enabled_headers,
            had_instance_send=had_instance_send,
            original_instance_send=original_instance_send,
        )
        wrapper_factory = cls._async_wrapper if isinstance(client, httpx.AsyncClient) else cls._sync_wrapper
        wrap_callable(client, "_send_single_request", wrapper_factory(state))
        # A weak reference keeps the registry from retaining the client indirectly.
        state.wrapper_ref = weakref.ref(getattr_static(client, "_send_single_request"))
        cls._clients[client] = state
        setattr(client, "_rollbar_httpx_context_propagation_instrumented", True)

    @classmethod
    def uninstrument_client(cls, client: httpx.Client | httpx.AsyncClient) -> None:
        """
        Disable propagating Rollbar baggage headers for a single HTTPX client.

        Note: This will not uninstrument the global configuration. To uninstrument the global configuration, you must
        call ``uninstrument()``.

        :param client: The HTTPX client to remove instrumentation from.
        :return: None
        """
        state = cls._clients.pop(client, None)
        if state is None:
            setattr(client, "_rollbar_httpx_context_propagation_instrumented", False)
            return
        state.active = False
        current_send = vars(client).get("_send_single_request")
        wrapper = state.wrapper_ref() if state.wrapper_ref is not None else None
        if current_send is wrapper:
            if state.had_instance_send:
                setattr(client, "_send_single_request", state.original_instance_send)
            else:
                delattr(client, "_send_single_request")
        setattr(client, "_rollbar_httpx_context_propagation_instrumented", False)
