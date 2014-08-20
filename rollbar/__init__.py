"""
Plugin for Pyramid apps to submit errors to Rollbar
"""

import copy
import inspect
import json
import logging
import socket
import sys
import threading
import time
import traceback
import types
import urllib
import uuid

import requests

try:
    # Python 3
    import urllib.parse as urlparse
    from urllib.parse import urlencode
    import reprlib
    string_types = (str, bytes)
except ImportError:
    # Python 2
    import urlparse
    from urllib import urlencode
    import repr as reprlib
    string_types = types.StringTypes


# import request objects from various frameworks, if available
try:
    from webob import BaseRequest as WebobBaseRequest
except ImportError:
    WebobBaseRequest = None

try:
    from django.core.exceptions import ImproperlyConfigured
except ImportError:
    DjangoHttpRequest = None
    RestFrameworkRequest = None

else:
    try:
        from django.http import HttpRequest as DjangoHttpRequest
    except (ImportError, ImproperlyConfigured):
        DjangoHttpRequest = None

    try:
        from rest_framework.request import Request as RestFrameworkRequest
    except (ImportError, ImproperlyConfigured):
        RestFrameworkRequest = None

    del ImproperlyConfigured

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


def get_request():
    """
    Get the current request object. Implementation varies on
    library support. Modified below when we know which framework
    is being used.
    """

    # TODO(cory): add in a generic _get_locals_request() which
    # will iterate up through the call stack and look for a variable
    # that appears to be valid request object.
    for fn in (_get_bottle_request,
               _get_flask_request,
               _get_pyramid_request,
               _get_pylons_request):
        try:
            req = fn()
            if req is not None:
                return req
        except:
            pass

    return None


def _get_bottle_request():
    from bottle import request
    return request


def _get_flask_request():
    from flask import request
    return request


def _get_pyramid_request():
    from pyramid.threadlocal import get_current_request
    return get_current_request()


def _get_pylons_request():
    from pylons import request
    return request


BASE_DATA_HOOK = None

log = logging.getLogger(__name__)

agent_log = None

VERSION = '0.9.0'
DEFAULT_ENDPOINT = 'https://api.rollbar.com/api/1/'
DEFAULT_TIMEOUT = 3

DEFAULT_LOCALS_SIZES = {
    'maxdict': 10,
    'maxarray': 10,
    'maxlist': 10,
    'maxtuple': 10,
    'maxset': 10,
    'maxfrozenset': 10,
    'maxdeque': 10,
    'maxstring': 100,
    'maxlong': 40,
    'maxother': 100,
}

# configuration settings
# configure by calling init() or overriding directly
SETTINGS = {
    'access_token': None,
    'enabled': True,
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
    'locals': {
        'enabled': True,
        'sizes': DEFAULT_LOCALS_SIZES
    }
}

# Set in init()
_repr = None

_initialized = False

# Do not call repr() on these types while gathering local variables
blacklisted_local_types = []


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
    global SETTINGS, agent_log, _initialized, _repr

    if not _initialized:
        _initialized = True

        SETTINGS['access_token'] = access_token
        SETTINGS['environment'] = environment

        # Merge the extra config settings into SETTINGS
        SETTINGS = dict_merge(SETTINGS, kw)

        if SETTINGS.get('allow_logging_basic_config'):
            logging.basicConfig()

        if SETTINGS.get('handler') == 'agent':
            agent_log = _create_agent_log()

        _repr = reprlib.Repr()
        for name, size in SETTINGS['locals']['sizes'].items():
            setattr(_repr, name, size)


def report_exc_info(exc_info=None, request=None, extra_data=None, payload_data=None, level=None, **kw):
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
        return _report_exc_info(exc_info, request, extra_data, payload_data, level=level)
    except Exception as e:
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
        return _report_message(message, level, request, extra_data, payload_data)
    except Exception as e:
        log.exception("Exception while reporting message to Rollbar. %r", e)


def send_payload(payload):
    """
    Sends a payload object, (the result of calling _build_payload()).
    Uses the configured handler from SETTINGS['handler']

    Available handlers:
    - 'blocking': calls _send_payload() (which makes an HTTP request) immediately, blocks on it
    - 'thread': starts a single-use thread that will call _send_payload(). returns immediately.
    - 'agent': writes to a log file to be processed by rollbar-agent
    """
    handler = SETTINGS.get('handler')
    if handler == 'blocking':
        _send_payload(payload)
    elif handler == 'agent':
        payload = ErrorIgnoringJSONEncoder().encode(payload)
        agent_log.error(payload)
    else:
        # default to 'thread'
        thread = threading.Thread(target=_send_payload, args=(payload,))
        thread.start()


def search_items(title, return_fields=None, access_token=None, endpoint=None, **search_fields):
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
                    endpoint=endpoint,
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
    def __init__(self, access_token, path, page_num, params, data, endpoint=None):
        super(PagedResult, self).__init__(access_token, path, params, data)
        self.page = page_num
        self.endpoint = endpoint

    def next_page(self):
        params = copy.copy(self.params)
        params['page'] = self.page + 1
        return _get_api(self.path, endpoint=self.endpoint, **params)

    def prev_page(self):
        if self.page <= 1:
            return self
        params = copy.copy(self.params)
        params['page'] = self.page - 1
        return _get_api(self.path, endpoint=self.endpoint, **params)


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


def _report_exc_info(exc_info, request, extra_data, payload_data, level=None):
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

    # explicitly override the level with provided level
    if level:
        data['level'] = level

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

    _add_locals_data(data, exc_info)
    _add_request_data(data, request)
    _add_person_data(data, request)
    data['server'] = _build_server_data()

    if payload_data:
        data = dict_merge(data, payload_data)

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
        data = dict_merge(data, payload_data)

    payload = _build_payload(data)
    send_payload(payload)

    return data['uuid']


def _check_config():
    if not SETTINGS.get('enabled'):
        log.info("pyrollbar: Not reporting because rollbar is disabled.")
        return False

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
        'language': 'python %s' % '.'.join(str(x) for x in sys.version_info[:3]),
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
    except Exception as e:
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


def _get_func_from_frame(frame):
    func_name = inspect.getframeinfo(frame).function
    caller = frame.f_back
    if caller:
        func = caller.f_locals.get(func_name,
                                   caller.f_globals.get(func_name))
    else:
        func = None

    return func


def _add_locals_data(data, exc_info):
    if not SETTINGS['locals']['enabled']:
        return

    frames = data['body']['trace']['frames']

    cur_tb = exc_info[2]
    frame_num = 0
    num_frames = len(frames)
    while cur_tb:
        cur_frame = frames[frame_num]
        tb_frame = cur_tb.tb_frame
        cur_tb = cur_tb.tb_next

        if not isinstance(tb_frame, types.FrameType):
            # this can happen if the traceback or frame is wrapped in some way,
            # for example by `ExceptionInfo` in
            # https://github.com/celery/billiard/blob/master/billiard/einfo.py
            log.warning('Traceback frame not a types.FrameType. Ignoring.')
            frame_num += 1
            continue

        # Create placeholders for args/kwargs/locals
        args = []
        kw = {}
        _locals = {}

        try:
            arginfo = inspect.getargvalues(tb_frame)
            local_vars = arginfo.locals

            func = _get_func_from_frame(tb_frame)
            if func:
                argspec = inspect.getargspec(func)
            else:
                argspec = None

            # Fill in all of the named args
            for named_arg in arginfo.args:
                args.append(_local_repr(local_vars[named_arg]))

            # Add any varargs
            if arginfo.varargs is not None:
                args.extend(map(_local_repr, local_vars[arginfo.varargs]))

            # Fill in all of the kwargs
            if arginfo.keywords is not None:
                kw.update(dict((k, _local_repr(v)) for k, v in local_vars[arginfo.keywords].items()))

            if argspec and argspec.defaults:
                # Put any of the args that have defaults into kwargs
                num_defaults = len(argspec.defaults)
                if num_defaults:
                    # The last len(argspec.defaults) args in arginfo.args should be added
                    # to kwargs and removed from args
                    kw.update(dict(zip(arginfo.args[-num_defaults:], args[-num_defaults:])))
                    args = args[:-num_defaults]

            # Optionally fill in locals for this frame
            if local_vars and _check_add_locals(cur_frame, frame_num, num_frames):
                _locals.update(dict((k, _local_repr(v)) for k, v in local_vars.items()))

            args = _scrub_obj(args)
            kw = _scrub_obj(kw)
            _locals = _scrub_obj(_locals)

        except Exception as e:
            log.exception('Error while extracting arguments from frame. Ignoring.')

        if args:
            cur_frame['args'] = args
        if kw:
            cur_frame['kwargs'] = kw
        if _locals:
            cur_frame['locals'] = _locals

        frame_num += 1


def _add_request_data(data, request):
    """
    Attempts to build request data; if successful, sets the 'request' key on `data`.
    """
    try:
        request_data = _build_request_data(request)
        request_data = _scrub_request_data(request_data)
    except Exception as e:
        log.exception("Exception while building request_data for Rollbar payload: %r", e)
    else:
        if request_data:
            data['request'] = request_data


def _check_add_locals(frame, frame_num, total_frames):
    """
    Returns True if we should record local variables for the given frame.
    """
    # Include the last frames locals
    # Include any frame locals that came from a file in the project's root
    return any(((frame_num == total_frames - 1),
                ('root' in SETTINGS and (frame.get('filename') or '').lower().startswith((SETTINGS['root'] or '').lower()))))


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

    # django rest framework
    if RestFrameworkRequest and isinstance(request, RestFrameworkRequest):
        return _build_django_request_data(request)

    # werkzeug (flask)
    if WerkzeugRequest and isinstance(request, WerkzeugRequest):
        return _build_werkzeug_request_data(request)

    if WerkzeugLocalProxy and isinstance(request, WerkzeugLocalProxy):
        actual_request = request._get_current_object()
        return _build_werkzeug_request_data(actual_request)

    # tornado
    if TornadoRequest and isinstance(request, TornadoRequest):
        return _build_tornado_request_data(request)

    # bottle
    if BottleRequest and isinstance(request, BottleRequest):
        return _build_bottle_request_data(request)

    return None


def _scrub_request_data(request_data):
    """
    Scrubs out sensitive information out of request data
    """
    if request_data:
        if request_data.get('POST'):
            request_data['POST'] = _scrub_obj(request_data['POST'])

        if request_data.get('GET'):
            request_data['GET'] = _scrub_obj(request_data['GET'])

        if request_data.get('url'):
            request_data['url'] = _scrub_request_url(request_data['url'])

    return request_data


def _scrub_request_url(url_string):
    url = urlparse.urlparse(url_string)
    qs_params = urlparse.parse_qs(url.query)

    # use dash for replacement character so it looks better since it wont be url escaped
    scrubbed_qs_params = _scrub_obj(qs_params, replacement_character='-')

    # Make sure the keys and values are all utf8-encoded strings
    scrubbed_qs_params = dict((_to_str(k), list(map(_to_str, v))) for k, v in scrubbed_qs_params.items())
    scrubbed_qs = urlencode(scrubbed_qs_params, doseq=True)

    scrubbed_url = (url.scheme, url.netloc, url.path, url.params, scrubbed_qs, url.fragment)
    scrubbed_url_string = urlparse.urlunparse(scrubbed_url)

    return scrubbed_url_string


def _scrub_obj(obj, replacement_character='*'):
    """
    Given an object, (e.g. dict/list/string) return the same object with sensitive
    data scrubbed out, (replaced with astrickses.)

    Fields to scrub out are defined in SETTINGS['scrub_fields'].
    """
    scrub_fields = set(SETTINGS['scrub_fields'])

    def _scrub(obj, k=None):
        if k is not None and _in_scrub_fields(k, scrub_fields):
            if isinstance(obj, string_types):
                return replacement_character * len(obj)
            elif isinstance(obj, list):
                return [_scrub(v, k) for v in obj]
            elif isinstance(obj, dict):
                return {replacement_character: replacement_character}
            else:
                return replacement_character
        elif isinstance(obj, dict):
            return dict((_k,  _scrub(v, _k)) for _k, v in obj.items())
        elif isinstance(obj, list):
            return [_scrub(x, k) for x in obj]
        else:
            return obj

    return _scrub(obj)


def _to_str(x):
    try:
        return str(x)
    except UnicodeEncodeError:
        try:
            return unicode(x).encode('utf8')
        except UnicodeEncodeError:
            return x.encode('utf8')


def _in_scrub_fields(val, scrub_fields):
    val = _to_str(val).lower()
    for field in set(scrub_fields):
        field = _to_str(field)
        if field == val:
            return True

    return False


def _local_repr(obj):
    if isinstance(obj, tuple(blacklisted_local_types)):
        return type(obj)

    orig = repr(obj)
    reprd = _repr.repr(obj)
    if reprd == orig:
        return obj
    else:
        return reprd


def _build_webob_request_data(request):
    request_data = {
        'url': request.url,
        'GET': dict(request.GET),
        'user_ip': _extract_user_ip(request),
        'headers': dict(request.headers),
    }

    try:
        if request.json:
            request_data['body'] = request.body
    except:
        pass

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

    try:
        request_data['body'] = request.body
    except:
        pass

    # headers
    headers = {}
    for k, v in request.environ.items():
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

    if request.get_json():
        request_data['body'] = json.dumps(_scrub_obj(request.json))

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
        'GET': dict(request.query)
    }

    if request.json:
        try:
            request_data['body'] = request.body.getvalue()
        except:
            pass
    else:
        request_data['POST'] = dict(request.forms)

    return request_data

def _build_server_data():
    """
    Returns a dictionary containing information about the server environment.
    """
    # server environment
    server_data = {
        'host': socket.gethostname(),
        'argv': sys.argv
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
    return payload


def _send_payload(payload):
    try:
        _post_api('item/', payload, access_token=payload.get('access_token'))
    except Exception as e:
        log.exception('Exception while posting item %r', e)


def _post_api(path, payload, access_token=None):
    headers = {'Content-Type': 'application/json'}

    if access_token is not None:
        headers['X-Rollbar-Access-Token'] = access_token

    # Serialize this ourselves so we can handle error cases more gracefully
    payload = ErrorIgnoringJSONEncoder().encode(payload)

    url = urlparse.urljoin(SETTINGS['endpoint'], path)
    resp = requests.post(url, data=payload, headers=headers, timeout=SETTINGS.get('timeout', DEFAULT_TIMEOUT))
    return _parse_response(path, SETTINGS['access_token'], payload, resp)


def _get_api(path, access_token=None, endpoint=None, **params):
    access_token = access_token or SETTINGS['access_token']
    url = urlparse.urljoin(endpoint or SETTINGS['endpoint'], path)
    params['access_token'] = access_token
    resp = requests.get(url, params=params)
    return _parse_response(path, access_token, params, resp, endpoint=endpoint)


def _parse_response(path, access_token, params, resp, endpoint=None):
    if resp.status_code == 429:
        log.warning("Rollbar: over rate limit, data was dropped. Payload was: %r", params)
        return
    elif resp.status_code != 200:
        log.warning("Got unexpected status code from Rollbar api: %s\nResponse:\n%s",
            resp.status_code, resp.text)

    try:
        data = resp.text
    except Exception as e:
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
            return PagedResult(access_token, path, result['page'], params, result, endpoint=endpoint)
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


# http://www.xormedia.com/recursively-merge-dictionaries-in-python.html
def dict_merge(a, b):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
    both a and bhave a key who's value is a dict then dict_merge is called
    on both values and the result stored in the returned dictionary.'''
    if not isinstance(b, dict):
        return b

    result = a
    for k, v in b.items():
        if k in result and isinstance(result[k], dict):
            result[k] = dict_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


class ErrorIgnoringJSONEncoder(json.JSONEncoder):
    def __init__(self, **kw):
        kw.setdefault('skipkeys', True)
        super(ErrorIgnoringJSONEncoder, self).__init__(**kw)

    def default(self, o):
        try:
            return _repr.repr(o)
        except:
            try:
                return str(o)
            except:
                return "<Unencodable object>"
