import asyncio
import inspect
import sys

from rollbar.contrib.asgi import ASGIApp


def run(coro):
    if sys.version_info >= (3, 7):
        return asyncio.run(coro)

    assert inspect.iscoroutine(coro)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def async_receive(message):
    async def receive():
        return message

    assert message["type"] == "http.request"
    return receive


@ASGIApp
class FailingTestASGIApp:
    def __call__(self, scope, receive, send):
        run(self._asgi_app(scope, receive, send))

    async def app(self, scope, receive, send):
        raise RuntimeError("Invoked only for testing")
