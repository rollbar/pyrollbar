from __future__ import annotations
import logging
import sys
from collections.abc import Iterable
from typing import cast, TYPE_CHECKING

import rollbar
from .integration import IntegrationBase, integrate
from .types import ASGIApp, Receive, Scope, Send
from rollbar.lib._async import RollbarAsyncError, try_report
from rollbar.lib.session import set_current_session, reset_current_session

if TYPE_CHECKING:
    from _typeshed import ExcInfo

log = logging.getLogger(__name__)


@integrate(framework_name='asgi')
class ReporterMiddleware(IntegrationBase):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__()

        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] == 'http':
            set_current_session(self._format_headers(scope['headers']))
        try:
            await self.app(scope, receive, send)
        except Exception:
            if scope['type'] == 'http':
                exc_info = cast('ExcInfo', sys.exc_info())

                try:
                    await try_report(exc_info)
                except RollbarAsyncError:
                    log.warning(
                        'Failed to report asynchronously. Trying to report synchronously.'
                    )
                    rollbar.report_exc_info(exc_info)
            raise
        finally:
            if scope['type'] == 'http':
                reset_current_session()

    @staticmethod
    def _format_headers(headers: Iterable[tuple[bytes, bytes]]) -> dict[str, str]:
        """
        Convert list of header tuples to a dictionary with string keys and values.

        Headers are expected to be in the format: [(b'header-name', b'header-value'), ...]
        """
        return {key.decode('latin-1'): value.decode('latin-1') for key, value in headers}
