import unittest
import sys

from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 5)


@unittest.skipUnless(ALLOWED_PYTHON_VERSION, 'ASGI implementation requires Python3.5+')
class IntegrationTest(BaseTest):
    def test_should_integrate_if__integrate_defined(self):
        from rollbar.contrib.asgi.integration import IntegrationBase

        called = False  # cannot patch local objects

        class Integration(IntegrationBase):
            def _integrate(self):
                nonlocal called
                called = True

        self.assertTrue(hasattr(Integration, '_integrate'))

        obj = Integration()

        self.assertTrue(called)
        self.assertTrue(hasattr(obj, '_integrate'))

    def test_should_not_fail_if__integrate_not_exists(self):
        from rollbar.contrib.asgi.integration import IntegrationBase

        class WrongIntegration(IntegrationBase):
            ...

        self.assertFalse(hasattr(WrongIntegration, '_integrate'))

        obj = WrongIntegration()

        self.assertFalse(hasattr(obj, '_integrate'))
