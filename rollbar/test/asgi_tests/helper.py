import asyncio
import functools

from rollbar.contrib.asgi import ASGIApp


def async_test_func_wrapper(asyncfunc):
    @functools.wraps(asyncfunc)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(asyncfunc(*args, **kwargs))
            finally:
                loop.close()
        else:
            loop.run_until_complete(asyncfunc(*args, **kwargs))
    return wrapper


@ASGIApp
class FailingTestASGIApp:
    def __init__(self):
        self.asgi_app = async_test_func_wrapper(self.asgi_app)

    async def app(self, scope, receive, send):
        raise RuntimeError("Invoked only for testing")
