"""
Plugin for Pyramid apps to submit errors to Ratchet.io
"""

import copy
import json
import logging
import socket
import threading
import time
import traceback
import urlparse

import requests

# import request objects from various frameworks, if available
try:
    from webob import BaseRequest as WebobBaseRequest
except ImportError:
    WebobBaseRequest = None

try:
    from django.http import HttpRequest as DjangoHttpRequest
except ImportError:
    DjangoHttpRequest = None

try:
    from werkzeug.wrappers import Request as WerkzeugRequest
except ImportError:
    WerkzeugRequest = None

try:
    from werkzeug.local import LocalProxy as WerkzeugLocalProxy
except ImportError:
    WerkzeugLocalProxy = None

try:
    from tornado.httpserver import HTTPRequest as TornadoRequest
except ImportError:
    TornadoRequest = None


log = logging.getLogger(__name__)
logging.basicConfig()

VERSION = '0.1.9'
DEFAULT_ENDPOINT = 'https://submit.ratchet.io/api/1/'

# configuration settings
# configure by calling init() or overriding directly
SETTINGS = {
    'access_token': None,
    'environment': 'production',
    'root': None,  # root path to your code
    'branch': None,  # git branch name
    'handler': 'thread',  # 'blocking' or 'thread'
    'endpoint': DEFAULT_ENDPOINT,
    'timeout': 1,
    'notifier': {
        'name': 'pyratchet',
        'version': VERSION
    },
}


## public api

def init(access_token, environment='production', **kw):
    """
    Saves configuration variables in this module's SETTINGS.

    access_token: project access token. Get this from the Ratchet.io UI:
                  - click "Settings" in the top nav
                  - click "Projects" in the left nav
                  - copy-paste the appropriate token.
    environment: environment name. Can be any string; suggestions: 'production', 'development',
                 'staging', 'yourname'
    **kw: provided keyword arguments will override keys in SETTINGS.
    """
    SETTINGS['access_token'] = access_token
    SETTINGS['environment'] = environment
    SETTINGS.update(kw)


def report_exc_info(exc_info, request=None, **kw):
    """
    Reports an exception to Ratchet, using exc_info (from calling sys.exc_info()) and an optional
    WebOb or Werkzeug-based request object.
    Any keyword args will be applied last and override what's built here.

    Example usage:

    ratchet.init(access_token='YOUR_PROJECT_ACCESS_TOKEN')
    try:
        do_something()
    except:
        ratchet.report_exc_info(sys.exc_info())
    """
    try:
        _report_exc_info(exc_info, request, **kw)
    except Exception, e:
        log.exception("Exception while reporting exc_info to Ratchet. %r", e)


def report_message(message, level='error', request=None, **kw):
    """
    Reports an arbitrary string message to Ratchet.
    """
    try:
        _report_message(message, level, request, **kw)
    except Exception, e:
        log.exception("Exception while reporting message to Ratchet. %r", e)


def send_payload(payload):
    """
    Sends a fully-formed payload (i.e. a string from json.dumps()).
    Uses the configured handler from SETTINGS['handler']

    Available handlers:
    - 'blocking': calls _send_payload() (which makes an HTTP request) immediately, blocks on it
    - 'thread': starts a single-use thread that will call _send_payload(). returns immediately.
    """
    handler = SETTINGS.get('handler')
    if handler == 'blocking':
        _send_payload(payload)
    else:
        # default to 'thread'
        thread = threading.Thread(target=_send_payload, args=(payload,))
        thread.start()


def search_items(title, return_fields=None, access_token=None, **search_fields):
    """
    Searches a project for items that match the input criteria.

    title: all or part of the item's title to search for.
    return_fields: the fields that should be returned for each item.
            e.g. ['id', 'project_id', 'status'] will return a dict containing
                 only those fields for each item.
    access_token: a project access token. If this is not provided,
                  the one provided to init() will be used instead.
    search_fields: additional fields to include in the search.
            currently supported: status, level, environment
    """
    if not title:
        return []

    if return_fields is not None:
        return_fields = ','.join(return_fields)

    return _get_api('search/',
                    title=title,
                    fields=return_fields,
                    access_token=access_token,
                    **search_fields)


class ApiException(Exception):
    """
    This exception will be raised if there was a problem decoding the
    response from an API call.
    """
    pass


class ApiError(ApiException):
    """
    This exception will be raised if the API response contains an 'err'
    field, denoting there was a problem fulfilling the api request.
    """
    pass


class Result(object):
    """
    This class encapsulates the response from an API call.
    Usage:

        result = search_items(title='foo', fields=['id'])
        print result.data
    """

    def __init__(self, access_token, path, params, data):
        self.access_token = access_token
        self.path = path
        self.params = params
        self.data = data

    def __str__(self):
        return str(self.data)


class PagedResult(Result):
    """
    This class wraps the response from an API call that responded with
    a page of results.
    Usage:

        result = search_items(title='foo', fields=['id'])
        print 'First page: %d, data: %s' % (result.page, result.data)
        result = result.next_page()
        print 'Second page: %d, data: %s' % (result.page, result.data)
    """
    def __init__(self, access_token, path, page_num, params, data):
        super(PagedResult, self).__init__(access_token, path, params, data)
        self.page = page_num

    def next_page(self):
        params = copy.copy(self.params)
        params['page'] = self.page + 1
        return _get_api(self.path, **params)

    def prev_page(self):
        if self.page <= 1:
            return self
        params = copy.copy(self.params)
        params['page'] = self.page - 1
        return _get_api(self.path, **params)


## internal functions

def _report_exc_info(exc_info, request=None, **kw):
    """
    Called by report_exc_info() wrapper
    """
    if not _check_config():
        return

    data = _build_base_data()

    # exception info
    cls, exc, trace = exc_info
    # most recent call last
    raw_frames = traceback.extract_tb(trace)
    frames = [{'filename': f[0], 'lineno': f[1], 'method': f[2], 'code': f[3]} for f in raw_frames]
    data['body'] = {
        'trace': {
            'frames': frames,
            'exception': {
                'class': cls.__name__,
                'message': str(exc),
            }
        }
    }

    _add_request_data(data, request)
    data['server'] = _build_server_data()

    payload = _build_payload(data)
    send_payload(payload)


def _report_message(message, level, request, **kw):
    """
    Called by report_message() wrapper
    """
    if not _check_config():
        return

    data = _build_base_data()
    data['level'] = level

    # message
    data['body'] = {
        'message': {
            'body': message
        }
    }

    _add_request_data(data, request)
    data['server'] = _build_server_data()

    payload = _build_payload(data)
    send_payload(payload)


def _check_config():
    # make sure we have an access_token
    if not SETTINGS.get('access_token'):
        log.warning("pyratchet: No access_token provided. Please configure by calling ratchet.init() with your access token.")
        return False
    return True


def _build_base_data(level='error'):
    return {
        'timestamp': int(time.time()),
        'environment': SETTINGS['environment'],
        'level': level,
        'language': 'python',
        'notifier': SETTINGS['notifier'],
    }


def _add_request_data(data, request):
    """
    Attempts to build request data; if successful, sets the 'request' key on `data`.
    """
    try:
        request_data = _build_request_data(request)
    except Exception, e:
        log.exception("Exception while building request_data for Ratchet payload: %r", e)
    else:
        if request_data:
            data['request'] = request_data


def _build_request_data(request):
    """
    Returns a dictionary containing data from the request.
    Can handle webob or werkzeug-based request objects.
    """

    # webob (pyramid)
    if WebobBaseRequest and isinstance(request, WebobBaseRequest):
        return _build_webob_request_data(request)

    # django
    if DjangoHttpRequest and isinstance(request, DjangoHttpRequest):
        return _build_django_request_data(request)

    # werkzeug (flask)
    if WerkzeugRequest and isinstance(request, WerkzeugRequest):
        return _build_werkzeug_request_data(request)

    if WerkzeugLocalProxy and isinstance(request, WerkzeugLocalProxy):
        actual_request = request._get_current_object()
        return _build_werkzeug_request_data(request)

    # tornado
    if TornadoRequest and isinstance(request, TornadoRequest):
        return _build_tornado_request_data(request)

    return None


def _build_webob_request_data(request):
    request_data = {
        'url': request.url,
        'GET': dict(request.GET),
        'user_ip': _extract_user_ip(request),
        'headers': dict(request.headers),
    }

    # pyramid matchdict
    if getattr(request, 'matchdict', None):
        request_data['params'] = request.matchdict

    # workaround for webob bug when the request body contains binary data but has a text
    # content-type
    try:
        request_data['POST'] = dict(request.POST)
    except UnicodeDecodeError:
        request_data['body'] = request.body

    return request_data


def _build_django_request_data(request):
    request_data = {
        'url': request.build_absolute_uri(),
        'method': request.method,
        'GET': dict(request.GET),
        'POST': dict(request.POST),
        'user_ip': _django_extract_user_ip(request),
    }

    # headers
    headers = {}
    for k, v in request.environ.iteritems():
        if k.startswith('HTTP_'):
            header_name = '-'.join(k[len('HTTP_'):].replace('_', ' ').title().split(' '))
            headers[header_name] = v
    request_data['headers'] = headers

    return request_data


def _build_werkzeug_request_data(request):
    request_data = {
        'url': request.url,
        'GET': dict(request.args),
        'POST': dict(request.form),
        'user_ip': _extract_user_ip(request),
        'headers': dict(request.headers),
        'method': request.method,
        'files_keys': request.files.keys(),
    }

    return request_data


def _build_tornado_request_data(request):
    request_data = {
        'url': request.uri,
        'user_ip': request.remote_ip,
        'headers': dict(request.headers),
        'method': request.method,
        'files_keys': request.files.keys(),
    }
    request_data[request.method] = request.arguments

    return request_data


def _build_server_data():
    """
    Returns a dictionary containing information about the server environment.
    """
    # server environment
    server_data = {
        'host': socket.gethostname(),
    }

    for key in ['branch', 'root']:
        if SETTINGS.get(key):
            server_data[key] = SETTINGS[key]

    return server_data


def _build_payload(data):
    """
    Returns the full payload as a string.
    """
    payload = {
        'access_token': SETTINGS['access_token'],
        'data': data
    }
    return json.dumps(payload)


def _send_payload(payload):
    return _post_api('item/', payload)


def _post_api(path, payload):
    url = urlparse.urljoin(SETTINGS['endpoint'], path)
    resp = requests.post(url, data=payload, timeout=SETTINGS.get('timeout', 1))
    return _parse_response(path, SETTINGS['access_token'], payload, resp)


def _get_api(path, access_token=None, **params):
    access_token = access_token or SETTINGS['access_token']
    url = urlparse.urljoin(SETTINGS['endpoint'], path)
    params['access_token'] = access_token
    resp = requests.get(url, params=params)
    return _parse_response(path, access_token, params, resp)


def _parse_response(path, access_token, params, resp):
    if resp.status_code != 200:
        log.warning("Got unexpected status code from Ratchet.io api: %s\nResponse:\n%s",
            resp.status_code, resp.text)

    data = resp.text
    try:
        json_data = json.loads(data)
    except (TypeError, ValueError):
        log.warning('Could not decode Ratchet.io api response:\n%s', data)
        raise ApiException('Request to %s returned invalid JSON response', path)
    else:
        if json_data.get('err'):
            raise ApiError(json_data.get('message') or 'Unknown error')

        result = json_data.get('result')

        if 'page' in result:
            return PagedResult(access_token, path, result['page'], params, result)
        else:
            return Result(access_token, path, params, result)


def _extract_user_ip(request):
    # some common things passed by load balancers... will need more of these.
    real_ip = request.headers.get('X-Real-Ip')
    if real_ip:
        return real_ip
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for
    return request.remote_addr


def _django_extract_user_ip(request):
    forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for
    real_ip = request.environ.get('HTTP_X_REAL_IP')
    if real_ip:
        return real_ip
    return request.environ['REMOTE_ADDR']



