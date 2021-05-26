import inspect
import sys

import unittest2

from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 5)


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'ASGI implementation requires Python3.5+')
class ASGISpecTest(BaseTest):
    def test_asgi_v3_middleware_is_single_callable_coroutine(self):
        from rollbar.contrib.asgi import ReporterMiddleware

        app = ReporterMiddleware(object)

        self.assertFalse(inspect.isclass(app))
        self.assertTrue(hasattr(app, '__call__'))
        self.assertTrue(inspect.iscoroutinefunction(app.__call__))

    def test_asgi_v3_app_signature(self):
        from rollbar.contrib.asgi import ReporterMiddleware

        app = ReporterMiddleware(object)
        app_args = inspect.getfullargspec(app).args

        self.assertListEqual(app_args, ['self', 'scope', 'receive', 'send'])
