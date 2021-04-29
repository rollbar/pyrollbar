import copy
import importlib
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import fastapi
import unittest2

import rollbar
import rollbar.contrib.fastapi
from rollbar.test import BaseTest


ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)
ALLOWED_FASTAPI_VERSION = fastapi.__version__ >= '0.41.0'


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'FastAPI requires Python3.6+')
class LoggingRouteUnsupportedFastAPIVersionTest(BaseTest):
    def test_should_disable_loading_route_handler_if_fastapi_is_too_old(self):
        import logging
        import fastapi
        from fastapi import FastAPI
        from fastapi.routing import APIRoute
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to
        from rollbar.contrib.fastapi.utils import FastAPIVersionError

        logging.disable()  # silent logger for tests
        fastapi_version = fastapi.__version__

        app = FastAPI()
        old_route_class = app.router.route_class
        self.assertEqual(old_route_class, APIRoute)

        fastapi.__version__ = '0'
        with self.assertRaises(FastAPIVersionError):
            rollbar_add_to(app)

        fastapi.__version__ = '0.30.3'
        with self.assertRaises(FastAPIVersionError):
            rollbar_add_to(app)

        fastapi.__version__ = '0.40.10'
        with self.assertRaises(FastAPIVersionError):
            rollbar_add_to(app)

        self.assertEqual(app.router.route_class, old_route_class)

        logging.disable(logging.NOTSET)  # make sure logger is re-enabled
        fastapi.__version__ = fastapi_version


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'FastAPI requires Python3.6+')
@unittest2.skipUnless(ALLOWED_FASTAPI_VERSION, 'FastAPI v0.41.0+ is required')
class LoggingRouteTest(BaseTest):
    default_settings = copy.deepcopy(rollbar.SETTINGS)

    def setUp(self):
        rollbar.SETTINGS = copy.deepcopy(self.default_settings)
        rollbar.SETTINGS['handler'] = 'async'
        importlib.reload(rollbar.contrib.fastapi)

    @mock.patch('rollbar.report_exc_info')
    def test_should_catch_and_report_errors(self, mock_report):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        app = FastAPI()
        rollbar_add_to(app)

        @app.get('/')
        async def read_root():
            1 / 0

        client = TestClient(app)
        with self.assertRaises(ZeroDivisionError):
            client.get('/')

        mock_report.assert_called_once()

        args, kwargs = mock_report.call_args
        self.assertEqual(kwargs, {})

        exc_type, exc_value, exc_tb = args[0]

        self.assertEqual(exc_type, ZeroDivisionError)
        self.assertIsInstance(exc_value, ZeroDivisionError)

    @mock.patch('rollbar.report_exc_info')
    def test_should_report_with_request_data(self, mock_report):
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        app = FastAPI()
        rollbar_add_to(app)

        @app.get('/')
        def read_root():
            1 / 0

        client = TestClient(app)
        with self.assertRaises(ZeroDivisionError):
            client.get('/')

        mock_report.assert_called_once()
        request = mock_report.call_args[0][1]

        self.assertIsInstance(request, Request)

    @mock.patch('rollbar._check_config', return_value=True)
    @mock.patch('rollbar._serialize_frame_data')
    @mock.patch('rollbar.send_payload')
    def test_should_send_payload_with_request_data(self, mock_send_payload, *mocks):
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        app = FastAPI()
        rollbar_add_to(app)

        @app.get('/{path}')
        def read_root(path):
            1 / 0

        client = TestClient(app)
        with self.assertRaises(ZeroDivisionError):
            client.get('/test?param1=value1&param2=value2')

        mock_send_payload.assert_called_once()
        payload = mock_send_payload.call_args[0][0]
        payload_request = payload['data']['request']

        self.assertEqual(payload_request['method'], 'GET')
        self.assertEqual(payload_request['user_ip'], 'testclient')
        self.assertEqual(
            payload_request['url'],
            'http://testserver/test?param1=value1&param2=value2',
        )
        self.assertDictEqual(payload_request['params'], {'path': 'test'})
        self.assertDictEqual(
            payload_request['GET'], {'param1': 'value1', 'param2': 'value2'}
        )
        self.assertDictEqual(
            payload_request['headers'],
            {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate',
                'connection': 'keep-alive',
                'host': 'testserver',
                'user-agent': 'testclient',
            },
        )

    @mock.patch('rollbar.lib._async.report_exc_info')
    @mock.patch('rollbar.report_exc_info')
    def test_should_use_async_report_exc_info_if_default_handler(
        self, sync_report_exc_info, async_report_exc_info
    ):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import rollbar
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        rollbar.SETTINGS['handler'] = 'default'

        app = FastAPI()
        rollbar_add_to(app)

        @app.get('/')
        async def root():
            1 / 0

        client = TestClient(app)
        with self.assertRaises(ZeroDivisionError):
            client.get('/')

        async_report_exc_info.assert_called_once()
        sync_report_exc_info.assert_not_called()

    @mock.patch('rollbar.lib._async.report_exc_info')
    @mock.patch('rollbar.report_exc_info')
    def test_should_use_async_report_exc_info_if_any_async_handler(
        self, sync_report_exc_info, async_report_exc_info
    ):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import rollbar
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        rollbar.SETTINGS['handler'] = 'httpx'

        app = FastAPI()
        rollbar_add_to(app)

        @app.get('/')
        async def root():
            1 / 0

        client = TestClient(app)
        with self.assertRaises(ZeroDivisionError):
            client.get('/')

        async_report_exc_info.assert_called_once()
        sync_report_exc_info.assert_not_called()

    @mock.patch('rollbar.lib._async.report_exc_info')
    @mock.patch('rollbar.report_exc_info')
    def test_should_use_sync_report_exc_info_if_non_async_handlers(
        self, sync_report_exc_info, async_report_exc_info
    ):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import rollbar
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        rollbar.SETTINGS['handler'] = 'threading'

        app = FastAPI()
        rollbar_add_to(app)

        @app.get('/')
        async def root():
            1 / 0

        client = TestClient(app)
        with self.assertRaises(ZeroDivisionError):
            client.get('/')

        sync_report_exc_info.assert_called_once()
        async_report_exc_info.assert_not_called()

    def test_should_enable_loading_route_handler_if_fastapi_version_is_sufficient(self):
        from fastapi import FastAPI
        from fastapi.routing import APIRoute
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to
        from rollbar.contrib.fastapi.routing import RollbarLoggingRoute

        self.assertTrue(ALLOWED_FASTAPI_VERSION)
        app = FastAPI()
        old_route_class = app.router.route_class
        self.assertEqual(old_route_class, APIRoute)

        new_route_class = rollbar_add_to(app)

        self.assertNotEqual(new_route_class, old_route_class)
        self.assertEqual(app.router.route_class, new_route_class)
        self.assertEqual(app.router.route_class, RollbarLoggingRoute)

    def test_should_enable_loading_route_handler_before_adding_routes_to_app(self):
        from fastapi import FastAPI
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to
        from rollbar.contrib.fastapi.routing import RollbarLoggingRoute

        app = FastAPI()
        old_route_class = app.router.route_class
        self.assertEqual(len(app.routes), 4)

        new_route_class = rollbar_add_to(app)

        self.assertNotEqual(new_route_class, old_route_class)
        self.assertEqual(app.router.route_class, new_route_class)
        self.assertEqual(len(app.routes), 4)

        @app.get('/')
        async def read_root():
            ...

        self.assertEqual(app.router.route_class, new_route_class)
        self.assertEqual(app.router.route_class, RollbarLoggingRoute)
        self.assertEqual(len(app.routes), 5)

    @mock.patch('logging.Logger.error')
    def test_should_disable_loading_route_handler_after_adding_routes_to_app(
        self, mock_log
    ):
        from fastapi import FastAPI
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        app = FastAPI()
        old_route_class = app.router.route_class
        self.assertEqual(len(app.routes), 4)

        @app.get('/')
        async def read_root():
            ...

        self.assertEqual(len(app.routes), 5)

        new_route_class = rollbar_add_to(app)

        self.assertEqual(len(app.routes), 5)
        self.assertIsNone(new_route_class)
        self.assertEqual(app.router.route_class, old_route_class)
        mock_log.assert_called_once_with(
            'RollbarLoggingRoute must to be added to a bare router'
            ' (before adding routes). See docs for more details.'
        )

    def test_should_enable_loading_route_handler_before_adding_routes_to_router(self):
        from fastapi import APIRouter, FastAPI
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to
        from rollbar.contrib.fastapi.routing import RollbarLoggingRoute

        app = FastAPI()
        router = APIRouter()

        old_app_route_class = app.router.route_class
        old_router_route_class = router.route_class

        self.assertEqual(len(app.routes), 4)
        self.assertEqual(len(router.routes), 0)

        new_route_class = rollbar_add_to(router)

        self.assertNotEqual(new_route_class, old_router_route_class)
        self.assertEqual(router.route_class, new_route_class)
        self.assertEqual(router.route_class, RollbarLoggingRoute)
        self.assertEqual(app.router.route_class, old_app_route_class)
        self.assertEqual(len(app.routes), 4)
        self.assertEqual(len(router.routes), 0)

        @router.get('/')
        async def read_root():
            ...

        app.include_router(router)

        self.assertEqual(router.route_class, new_route_class)
        self.assertEqual(len(app.routes), 5)

    @mock.patch('logging.Logger.error')
    def test_should_disable_loading_route_handler_after_adding_routes_to_router(
        self, mock_log
    ):
        from fastapi import APIRouter, FastAPI
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        app = FastAPI()
        router = APIRouter()

        old_app_route_class = app.router.route_class
        old_router_route_class = router.route_class

        self.assertEqual(len(app.routes), 4)
        self.assertEqual(len(router.routes), 0)

        @router.get('/')
        async def read_root():
            ...

        app.include_router(router)
        self.assertEqual(len(app.routes), 5)
        self.assertEqual(len(router.routes), 1)

        new_route_class = rollbar_add_to(app)

        self.assertEqual(len(app.routes), 5)
        self.assertEqual(len(router.routes), 1)
        self.assertIsNone(new_route_class)
        self.assertEqual(app.router.route_class, old_app_route_class)
        self.assertEqual(router.route_class, old_router_route_class)
        mock_log.assert_called_once_with(
            'RollbarLoggingRoute must to be added to a bare router'
            ' (before adding routes). See docs for more details.'
        )

    def test_should_enable_loading_route_handler_for_multiple_routers(self):
        from fastapi import APIRouter, FastAPI
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to
        from rollbar.contrib.fastapi.routing import RollbarLoggingRoute

        app = FastAPI()
        router1 = APIRouter()
        router2 = APIRouter()
        router3 = APIRouter()

        old_app_route_class = app.router.route_class
        old_router1_route_class = router1.route_class
        old_router2_route_class = router2.route_class
        old_router3_route_class = router3.route_class

        self.assertEqual(len(app.routes), 4)
        self.assertEqual(len(router1.routes), 0)
        self.assertEqual(len(router2.routes), 0)
        self.assertEqual(len(router3.routes), 0)

        new_router1_route_class = rollbar_add_to(router1)
        new_router2_route_class = rollbar_add_to(router2)

        self.assertNotEqual(new_router1_route_class, old_router1_route_class)
        self.assertNotEqual(new_router2_route_class, old_router2_route_class)
        self.assertEqual(router1.route_class, RollbarLoggingRoute)
        self.assertEqual(router2.route_class, RollbarLoggingRoute)
        self.assertEqual(router1.route_class, new_router1_route_class)
        self.assertEqual(router2.route_class, new_router2_route_class)
        self.assertEqual(router3.route_class, old_router3_route_class)
        self.assertEqual(app.router.route_class, old_app_route_class)
        self.assertEqual(len(app.routes), 4)
        self.assertEqual(len(router1.routes), 0)
        self.assertEqual(len(router2.routes), 0)
        self.assertEqual(len(router3.routes), 0)

        @router1.get('/')
        async def read1():
            ...

        @router2.get('/')
        async def read2():
            ...

        @router3.get('/')
        async def read3():
            ...

        app.include_router(router1)
        app.include_router(router2)
        app.include_router(router3)

        self.assertEqual(router1.route_class, new_router1_route_class)
        self.assertEqual(router2.route_class, new_router2_route_class)
        self.assertEqual(router3.route_class, old_router3_route_class)
        self.assertEqual(len(app.routes), 7)

    def test_should_enable_loading_route_handler_for_fastapi_app(self):
        from fastapi import FastAPI
        from fastapi.routing import APIRoute
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to
        from rollbar.contrib.fastapi.routing import RollbarLoggingRoute

        app = FastAPI()
        old_route_class = app.router.route_class
        self.assertEqual(old_route_class, APIRoute)

        new_route_class = rollbar_add_to(app)

        self.assertNotEqual(new_route_class, old_route_class)
        self.assertEqual(app.router.route_class, RollbarLoggingRoute)
        self.assertEqual(app.router.route_class, new_route_class)

    def test_should_enable_loading_route_handler_for_fastapi_router(self):
        from fastapi import APIRouter
        from fastapi.routing import APIRoute
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to
        from rollbar.contrib.fastapi.routing import RollbarLoggingRoute

        router = APIRouter()
        old_route_class = router.route_class
        self.assertEqual(old_route_class, APIRoute)

        new_route_class = rollbar_add_to(router)

        self.assertNotEqual(new_route_class, old_route_class)
        self.assertEqual(router.route_class, RollbarLoggingRoute)
        self.assertEqual(router.route_class, new_route_class)

    @mock.patch('logging.Logger.error')
    def test_should_disable_loading_route_handler_for_unknown_app(self, mock_log):
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        class UnkownRouter:
            route_class = None

        class UnknownApp:
            routes = []
            router = UnkownRouter()

        app = UnknownApp()
        old_route_class = app.router.route_class

        new_route_class = rollbar_add_to(app)

        self.assertIsNone(new_route_class)
        self.assertEqual(app.router.route_class, old_route_class)
        mock_log.assert_called_once_with(
            'Error adding RollbarLoggingRoute to application.'
        )

    @mock.patch('logging.Logger.error')
    def test_should_disable_loading_route_handler_for_unknown_router(self, mock_log):
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        class UnknownRouter:
            routes = []
            route_class = None

        router = UnknownRouter()
        old_route_class = router.route_class

        new_route_class = rollbar_add_to(router)

        self.assertIsNone(new_route_class)
        self.assertEqual(router.route_class, old_route_class)
        mock_log.assert_called_once_with(
            'Error adding RollbarLoggingRoute to application.'
        )

    def test_should_warn_if_middleware_in_use(self):
        from fastapi import FastAPI
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to
        from rollbar.contrib.fastapi import ReporterMiddleware as FastAPIMiddleware
        from rollbar.contrib.starlette import ReporterMiddleware as StarletteMiddleware
        from rollbar.contrib.asgi import ReporterMiddleware as ASGIMiddleware

        for middleware in (FastAPIMiddleware, StarletteMiddleware, ASGIMiddleware):
            with mock.patch('logging.Logger.warning') as mock_log:
                app = FastAPI()
                app.add_middleware(middleware)

                rollbar_add_to(app)

                mock_log.assert_called_once_with(
                    f'Detected middleware installed {[middleware]}'
                    ' while loading Rollbar route handler.'
                    ' This can cause in duplicate occurrences.'
                )

    @unittest2.skipUnless(
        sys.version_info >= (3, 7), 'Global request access requires Python 3.7+'
    )
    @mock.patch('rollbar.contrib.fastapi.routing.store_current_request')
    def test_should_store_current_request(self, store_current_request):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        expected_scope = {
            'client': ['testclient', 50000],
            'headers': [
                (b'host', b'testserver'),
                (b'user-agent', b'testclient'),
                (b'accept-encoding', b'gzip, deflate'),
                (b'accept', b'*/*'),
                (b'connection', b'keep-alive'),
            ],
            'http_version': '1.1',
            'method': 'GET',
            'path': '/',
            'query_string': b'',
            'root_path': '',
            'scheme': 'http',
            'server': ['testserver', 80],
            'type': 'http',
        }

        app = FastAPI()
        rollbar_add_to(app)

        @app.get('/')
        async def read_root():
            ...

        client = TestClient(app)
        client.get('/')

        store_current_request.assert_called_once()

        scope = store_current_request.call_args[0][0]
        self.assertDictContainsSubset(expected_scope, scope)

    @unittest2.skipUnless(
        sys.version_info >= (3, 7), 'Global request access is supported in Python 3.7+'
    )
    def test_should_return_current_request(self):
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi import get_current_request
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        app = FastAPI()
        rollbar_add_to(app)

        @app.get('/')
        async def read_root(original_request: Request):
            request = get_current_request()

            self.assertEqual(request, original_request)

        client = TestClient(app)
        client.get('/')

    @mock.patch('rollbar.contrib.starlette.requests.ContextVar', None)
    @mock.patch('logging.Logger.error')
    def test_should_not_return_current_request_for_older_python(self, mock_log):
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from rollbar.contrib.fastapi import get_current_request
        from rollbar.contrib.fastapi.routing import add_to as rollbar_add_to

        app = FastAPI()
        rollbar_add_to(app)

        @app.get('/')
        async def read_root(original_request: Request):
            request = get_current_request()

            self.assertIsNone(request)
            self.assertNotEqual(request, original_request)
            mock_log.assert_called_once_with(
                'Python 3.7+ is required to receive current request.'
            )

        client = TestClient(app)
        client.get('/')

    def test_should_support_type_hints(self):
        from typing import Optional, Type, Union
        from fastapi import APIRouter, FastAPI
        from fastapi.routing import APIRoute
        import rollbar.contrib.fastapi.routing

        self.assertDictEqual(
            rollbar.contrib.fastapi.routing.add_to.__annotations__,
            {
                'app_or_router': Union[FastAPI, APIRouter],
                'return': Optional[Type[APIRoute]],
            },
        )
