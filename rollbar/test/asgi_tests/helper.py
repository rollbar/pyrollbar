import asyncio
import functools
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


def wrap_async(asyncfunc):
    @functools.wraps(asyncfunc)
    def wrapper(*args, **kwargs):
        run(asyncfunc(*args, **kwargs))

    return wrapper


@ASGIApp
class FailingTestASGIApp:
    def __init__(self):
        self.asgi_app = wrap_async(self.asgi_app)

    async def app(self, scope, receive, send):
        raise RuntimeError("Invoked only for testing")
