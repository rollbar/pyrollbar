from rollbar.test import BaseTest


class FastAPIUtilsTest(BaseTest):
    def test_should_return_installed_rollbar_middlewares(self):
        from fastapi import FastAPI
        from rollbar.contrib.fastapi.utils import get_installed_middlewares
        from rollbar.contrib.fastapi import FastAPIMiddleware
        from rollbar.contrib.starlette import StarletteMiddleware
        from rollbar.contrib.asgi import ASGIMiddleware

        # single middleware
        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)

        middlewares = get_installed_middlewares(app)

        self.assertListEqual(middlewares, [FastAPIMiddleware])

        # multiple middlewares
        app = FastAPI()
        app.add_middleware(FastAPIMiddleware)
        app.add_middleware(StarletteMiddleware)
        app.add_middleware(ASGIMiddleware)

        middlewares = get_installed_middlewares(app)

        self.assertListEqual(
            middlewares, ([ASGIMiddleware, StarletteMiddleware, FastAPIMiddleware])
        )

    def test_should_return_empty_list_if_rollbar_middlewares_not_installed(self):
        from fastapi import FastAPI
        from rollbar.contrib.fastapi.utils import get_installed_middlewares
        from rollbar.test.async_helper import BareMiddleware

        # no middlewares
        app = FastAPI()

        middlewares = get_installed_middlewares(app)

        self.assertListEqual(middlewares, [])

        # no Rollbar middlewares
        app = FastAPI()
        app.add_middleware(BareMiddleware)

        middlewares = get_installed_middlewares(app)

        self.assertListEqual(middlewares, [])
