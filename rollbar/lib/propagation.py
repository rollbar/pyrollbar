from __future__ import annotations

import re
import typing
from urllib.parse import urlsplit, urlunsplit


HeaderValue = str | bytes
ROLLBAR_BAGGAGE_KEYS = frozenset({
    "rollbar.session.id",
    "rollbar.execution.scope.id",
})


def normalize_exact_url(url: str) -> str:
    """
    Normalize an exact URL for matching against request URLs.
    """
    try:
        parsed = urlsplit(url)
    except ValueError:
        return url

    if parsed.scheme and parsed.netloc and not parsed.path:
        # HTTP clients canonicalize an empty root path to "/".
        parsed = parsed._replace(path="/")
    return urlunsplit(parsed)


class URLMatcher:
    """
    Match request URLs without reparsing configured exact URLs per request.
    """

    def __init__(self, enabled_urls: typing.Iterable[str | re.Pattern[str]]) -> None:
        exact: set[str] = set()
        patterns: list[re.Pattern[str]] = []
        for value in enabled_urls:
            if isinstance(value, str):
                # Exact matches use a set so large allowlists stay cheap.
                exact.add(normalize_exact_url(value))
            else:
                patterns.append(value)
        self.exact_urls = frozenset(exact)
        self.patterns = tuple(patterns)

    def matches(self, url: object | None) -> bool:
        """
        Check if the given URL matches any of the configured exact URLs or patterns.

        :param url: The URL to check, which can be a string or any object that can be converted to a string.
        :return: True if the URL matches, False otherwise.
        """
        if url is None:
            return False
        normalized = normalize_exact_url(str(url))
        return normalized in self.exact_urls or any(
            pattern.match(normalized) for pattern in self.patterns
        )


def baggage_is_enabled(enabled_headers: typing.Iterable[str]) -> bool:
    """
    Returns True if the "baggage" header is enabled for propagation, False otherwise.
    """
    return any(header.lower() == "baggage" for header in enabled_headers)


def _header_text(value: HeaderValue) -> str:
    return value.decode("latin-1") if isinstance(value, bytes) else value


def has_rollbar_baggage(headers: typing.Mapping[str, HeaderValue]) -> bool:
    """
    Returns True if the "baggage" header contains any Rollbar session or execution scope keys, False otherwise.
    """
    existing = headers.get("baggage")
    if not existing:
        return False
    return any(
        member.partition("=")[0].strip().lower() in ROLLBAR_BAGGAGE_KEYS
        for member in _header_text(existing).split(",")
    )


def replace_rollbar_baggage(
        headers: typing.MutableMapping[str, HeaderValue],
        propagation_header: str | None,
) -> None:
    """
    Replaces Rollbar-related members in the "baggage" header with the provided propagation header.
    """
    existing = headers.get("baggage")
    members = (
        [member.strip() for member in _header_text(existing).split(",") if member.strip()]
        if existing else []
    )
    # Replace only Rollbar members; vendor baggage must pass through unchanged.
    members = [
        member for member in members
        if member.partition("=")[0].strip().lower() not in ROLLBAR_BAGGAGE_KEYS
    ]
    if propagation_header:
        members.extend(
            member.strip() for member in propagation_header.split(",") if member.strip()
        )
    if members:
        headers["baggage"] = ", ".join(members)
    else:
        headers.pop("baggage", None)
