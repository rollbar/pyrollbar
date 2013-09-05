"""
Plugin for Pyramid apps to submit errors to Rollbar
"""

import copy
import json
import logging
import socket
import sys
import threading
import time
import traceback
import urlparse
import urllib
import uuid

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

try:
    from bottle import BaseRequest as BottleRequest
except ImportError:
    BottleRequest = None
    
BASE_DATA_HOOK = None

log = logging.getLogger(__name__)

agent_log = None

VERSION = '0.5.10'
DEFAULT_ENDPOINT = 'https://api.rollbar.com/api/1/'
DEFAULT_TIMEOUT = 3

# configuration settings
# configure by calling init() or overriding directly
SETTINGS = {
    'access_token': None,
    'environment': 'production',
    'exception_level_filters': [],
    'root': None,  # root path to your code
    'branch': None,  # git branch name
    'code_version': None,
    'handler': 'thread',  # 'blocking', 'thread' or 'agent'
    'endpoint': DEFAULT_ENDPOINT,
    'timeout': DEFAULT_TIMEOUT,
    'agent.log_file': 'log.rollbar',
    'scrub_fields': ['passwd', 'password', 'secret', 'confirm_password', 'password_confirmation'],
    'notifier': {
        'name': 'pyrollbar',
        'version': VERSION
    },
    'allow_logging_basic_config': True,  # set to False to avoid a call to logging.basicConfig()
}

_initialized = False

## public api

def init(access_token, environment='production', **kw):
    """
    Saves configuration variables in this module's SETTINGS.

    access_token: project access token. Get this from the Rollbar UI:
                  - click "Settings" in the top nav
                  - click "Projects" in the left nav
                  - copy-paste the appropriate token.
    environment: environment name. Can be any string; suggestions: 'production', 'development',
                 'staging', 'yourname'
    **kw: provided keyword arguments will override keys in SETTINGS.
    """
    global agent_log, _initialized

    if not _initialized:
        _initialized = True

        SETTINGS['access_token'] = access_token
        SETTINGS['environment'] = environment
        SETTINGS.update(kw)

        if SETTINGS.get('allow_logging_basic_config'):
            logging.basicConfig()

        if SETTINGS.get('handler') == 'agent':
            agent_log = _create_agent_log()


def report_exc_info(exc_info=None, request=None, extra_data=None, payload_data=None, **kw):
    """
    Reports an exception to Rollbar, using exc_info (from calling sys.exc_info()) 
    
    exc_info: optional, should be the result of calling sys.exc_info(). If omitted, sys.exc_info() will be called here.
    request: optional, a WebOb or Werkzeug-based request object.
    extra_data: optional, will be included in the 'custom' section of the payload
    payload_data: optional, dict that will override values in the final payload 
                  (e.g. 'level' or 'fingerprint')
    kw: provided for legacy purposes; unused.

    Example usage:

    rollbar.init(access_token='YOUR_PROJECT_ACCESS_TOKEN')
    try:
        do_something()
    except:
        rollbar.report_exc_info(sys.exc_info(), request, {'foo': 'bar'}, {'level': 'warning'})
    """
    if exc_info is None:
        exc_info = sys.exc_info()
    
    try:
        return _report_exc_info(exc_info, request, extra_data, payload_data)
    except Exception, e:
        log.exception("Exception while reporting exc_info to Rollbar. %r", e)


def report_message(message, level='error', request=None, extra_data=None, payload_data=None):
    """
    Reports an arbitrary string message to Rollbar.

    message: the string body of the message
    level: level to report at. One of: 'critical', 'error', 'warning', 'info', 'debug'
    request: the request object for the context of the message
    extra_data: dictionary of params to include with the message. 'body' is reserved.
    payload_data: param names to pass in the 'data' level of the payload; overrides defaults.
    """
    try:
        _report_message(message, level, request, extra_data, payload_data)
    except Exception, e:
        log.exception("Exception while reporting message to Rollbar. %r", e)


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
    elif handler == 'agent':
        agent_log.error(json.dumps(payload))
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


def _filtered_level(exception):
    for cls, level in SETTINGS['exception_level_filters']:
        if isinstance(exception, cls):
            return level
    
    return None


def _is_ignored(exception):
    return _filtered_level(exception) == 'ignored'

    
def _create_agent_log():
    """
    Creates .rollbar log file for use with rollbar-agent
    """
    log_file = SETTINGS['agent.log_file']
    if not log_file.endswith('.rollbar'):
        log.error("Provided agent log file does not end with .rollbar, which it must. "
            "Using default instead.")
        log_file = DEFAULTS['agent.log_file']
    
    retval = logging.getLogger('rollbar_agent')
    handler = logging.FileHandler(log_file, 'a', 'utf-8')
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    retval.addHandler(handler)
    retval.setLevel(logging.WARNING)
    return retval


def _report_exc_info(exc_info, request, extra_data, payload_data):
    """
    Called by report_exc_info() wrapper
    """
    # check if exception is marked ignored
    cls, exc, trace = exc_info
    if getattr(exc, '_rollbar_ignore', False) or _is_ignored(exc):
        return

    if not _check_config():
        return
    
    data = _build_base_data(request)
    
    filtered_level = _filtered_level(exc)
    if filtered_level:
        data['level'] = filtered_level

    # exception info
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

    if extra_data:
        if isinstance(extra_data, dict):
            data['custom'] = extra_data
        else:
            data['custom'] = {'value': extra_data}

    _add_request_data(data, request)
    _add_person_data(data, request)
    data['server'] = _build_server_data()
    
    if payload_data:
        data.update(payload_data)

    payload = _build_payload(data)
    send_payload(payload)

    return data['uuid']


def _report_message(message, level, request, extra_data, payload_data):
    """
    Called by report_message() wrapper
    """
    if not _check_config():
        return

    data = _build_base_data(request, level=level)

    # message
    data['body'] = {
        'message': {
            'body': message
        }
    }

    if extra_data:
        data['body']['message'].update(extra_data)

    _add_request_data(data, request)
    _add_person_data(data, request)
    data['server'] = _build_server_data()

    if payload_data:
        data.update(payload_data)

    payload = _build_payload(data)
    send_payload(payload)

    return data['uuid']


def _check_config():
    # make sure we have an access_token
    if not SETTINGS.get('access_token'):
        log.warning("pyrollbar: No access_token provided. Please configure by calling rollbar.init() with your access token.")
        return False
    return True


def _build_base_data(request, level='error'):
    data = {
        'timestamp': int(time.time()),
        'environment': SETTINGS['environment'],
        'level': level,
        'language': 'python',
        'notifier': SETTINGS['notifier'],
        'uuid': str(uuid.uuid4()),
    }
    
    if SETTINGS.get('code_version'):
        data['code_version'] = SETTINGS['code_version']
    
    if BASE_DATA_HOOK:
        BASE_DATA_HOOK(request, data)
    
    return data


def _add_person_data(data, request):
    try:
        person_data = _build_person_data(request)
    except Exception, e:
        log.exception("Exception while building person data for Rollbar paylooad: %r", e)
    else:
        if person_data:
            data['person'] = person_data


def _build_person_data(request):
    """
    Returns a dictionary describing the logged-in user using data from `request.

    Try request.rollbar_person first, then 'user', then 'user_id'
    """
    if hasattr(request, 'rollbar_person'):
        rollbar_person_prop = request.rollbar_person
        try:
            person = rollbar_person_prop()
        except TypeError:
            person = rollbar_person_prop

        if person and isinstance(person, dict):
            return person
        else:
            return None

    if hasattr(request, 'user'):
        user_prop = request.user
        try:
            user = user_prop()
        except TypeError:
            user = user_prop

        if not user:
            return None
        elif isinstance(user, dict):
            return user
        else:
            retval = {}
            if getattr(user, 'id', None):
                retval['id'] = str(user.id)
            elif getattr(user, 'user_id', None):
                retval['id'] = str(user.user_id)

            # id is required, so only include username/email if we have an id
            if retval.get('id'):
                retval.update({
                    'username': getattr(user, 'username', None),
                    'email': getattr(user, 'email', None)
                })
            return retval

    if hasattr(request, 'user_id'):
        user_id_prop = request.user_id
        try:
            user_id = user_id_prop()
        except TypeError:
            user_id = user_id_prop
        
        if not user_id:
            return None
        return {'id': str(user_id)}
    

def _add_request_data(data, request):
    """
    Attempts to build request data; if successful, sets the 'request' key on `data`.
    """
    try:
        request_data = _build_request_data(request)
        request_data = _scrub_request_data(request_data)
    except Exception, e:
        log.exception("Exception while building request_data for Rollbar payload: %r", e)
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

    #bottle
    if BottleRequest and isinstance(request, BottleRequest):
        return _build_bottle_request_data(request)

    return None


def _scrub_request_data(request_data):
    """
    Scrubs out sensitive information out of request data
    """
    if request_data:
        if request_data.get('POST'):
            request_data['POST'] = _scrub_request_params(request_data['POST'])

        if request_data.get('GET'):
            request_data['GET'] = _scrub_request_params(request_data['GET'])

        if request_data.get('url'):
            request_data['url'] = _scrub_request_url(request_data['url'])

    return request_data


def _scrub_request_url(url_string):
    url = urlparse.urlparse(url_string)
    qs_params = urlparse.parse_qs(url.query)

    # use dash for replacement character so it looks better since it wont be url escaped
    scrubbed_qs_params = _scrub_request_params(qs_params, replacement_character='-')
    scrubbed_qs = urllib.urlencode(scrubbed_qs_params, doseq=True)

    scrubbed_url = (url.scheme, url.netloc, url.path, url.params, scrubbed_qs, url.fragment)
    scrubbed_url_string = urlparse.urlunparse(scrubbed_url)

    return scrubbed_url_string


def _scrub_request_params(params, replacement_character='*'):
    """
    Given request.POST/request.GET, returns a dict with passwords scrubbed out
    (replaced with astrickses)
    """
    scrub_fields = set(SETTINGS['scrub_fields'])
    params = dict(params)
    
    for k, v in params.items():
        if k.lower() in scrub_fields:
            if isinstance(v, list):
                params[k] = [replacement_character * len(x) for x in v]
            else:
                params[k] = replacement_character * len(v)
    
    return params


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
        'url': request.full_url(),
        'user_ip': request.remote_ip,
        'headers': dict(request.headers),
        'method': request.method,
        'files_keys': request.files.keys(),
    }
    request_data[request.method] = request.arguments

    return request_data

def _build_bottle_request_data(request):
    request_data = {
        'url': request.url,
        'user_ip': request.remote_addr,
        'headers': dict(request.headers),
        'method': request.method,
        'GET': dict(request.query),
        'POST': dict(request.forms),
    }

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
    return ErrorIgnoringJSONEncoder().encode(payload)


def _send_payload(payload):
    try:
        _post_api('item/', payload)
    except Exception, e:
        log.exception('Exception while posting item %r', e)


def _post_api(path, payload):
    url = urlparse.urljoin(SETTINGS['endpoint'], path)
    resp = requests.post(url, data=payload, timeout=SETTINGS.get('timeout', DEFAULT_TIMEOUT))
    return _parse_response(path, SETTINGS['access_token'], payload, resp)


def _get_api(path, access_token=None, **params):
    access_token = access_token or SETTINGS['access_token']
    url = urlparse.urljoin(SETTINGS['endpoint'], path)
    params['access_token'] = access_token
    resp = requests.get(url, params=params)
    return _parse_response(path, access_token, params, resp)


def _parse_response(path, access_token, params, resp):
    if resp.status_code == 429:
        log.warning("Rollbar: over rate limit, data was dropped. Payload was: %r", params)
        return
    elif resp.status_code != 200:
        log.warning("Got unexpected status code from Rollbar api: %s\nResponse:\n%s",
            resp.status_code, resp.text)
    
    try:
        data = resp.text
    except Exception, e:
        data = resp.content
        log.error('resp.text is undefined, resp.content is %r', resp.content)
    
    try:
        json_data = json.loads(data)
    except (TypeError, ValueError):
        log.warning('Could not decode Rollbar api response:\n%s', data)
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


class ErrorIgnoringJSONEncoder(json.JSONEncoder):
    def __init__(self, **kw):
        kw.setdefault('skipkeys', True)
        super(ErrorIgnoringJSONEncoder, self).__init__(**kw)

    def default(self, o):
        try:
            return repr(o)
        except:
            try:
                return str(o)
            except:
                return "<Unencodable object>"
