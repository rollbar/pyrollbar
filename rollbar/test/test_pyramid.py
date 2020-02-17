try:
    from unittest import mock
except ImportError:
    import mock

from rollbar.test import BaseTest

try:
    from pyramid.request import Request

    PYRAMID_INSTALLED = True
except ImportError:
    PYRAMID_INSTALLED = False


if PYRAMID_INSTALLED:

    class PyramidMiddlewareTest(BaseTest):
        def test_catch_exception_in_the_wsgi_app(self):
            from rollbar.contrib.pyramid import RollbarMiddleware

            def wsgi_app(environ, start_resp):
                raise RuntimeError("oops")

            middleware = RollbarMiddleware({}, wsgi_app)

            with mock.patch("rollbar.report_exc_info") as mock_report:
                with self.assertRaises(RuntimeError):
                    middleware(environ={}, start_resp=lambda: None)

            self.assertEqual(mock_report.call_count, 1)

            args, kwargs = mock_report.call_args
            self.assertEqual(kwargs, {})

            exc_info, request = args

            exc_type, exc_value, exc_tb = exc_info
            self.assertEqual(exc_type, RuntimeError)
            self.assertIsInstance(exc_value, RuntimeError)

            self.assertIsInstance(request, Request)
