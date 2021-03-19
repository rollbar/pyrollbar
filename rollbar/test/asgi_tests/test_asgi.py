import sys

import unittest2

from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info[0] >= 3 and sys.version_info[1] >= 5


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, "ASGI implementation requires Python3.5+")
class ASGIMiddlewareTest(BaseTest):
    def test_should_set_asgi_hook(self):
        import rollbar
        import rollbar.contrib.asgi

        self.assertEqual(rollbar.BASE_DATA_HOOK, rollbar.contrib.asgi._hook)

    def test_should_support_type_hints_if_starlette_installed(self):
        try:
            from starlette.types import ASGIApp, Receive, Scope, Send
        except ImportError:
            self.skipTest("Support for type hints requires Starlette to be installed")

        import rollbar.contrib.asgi

        self.assertDictEqual(
            rollbar.contrib.asgi.ASGIMiddleware.__call__.__annotations__,
            {"scope": Scope, "receive": Receive, "send": Send, "return": None},
        )
