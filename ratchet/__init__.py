"""
Plugin for Pyramid apps to submit errors to Ratchet.io
"""

import json
import logging
import socket
import sys
import threading
import time
import traceback

import requests

log = logging.getLogger(__name__)

VERSION = '0.1.5'
DEFAULT_ENDPOINT = 'https://submit.ratchet.io/api/1/item/'

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


def report_message(message, level='error', request=None, **kw):
    """
    Reports an arbitrary string message to Ratchet.
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


## internal functions

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
    request_data = _build_request_data(request)
    if request_data:
        data['request'] = request_data


def _build_request_data(request):
    """
    Returns a dictionary containing data from the request. 
    Can handle webob or werkzeug-based request objects.
    """
    try:
        import webob
    except ImportError:
        pass
    else:
        if isinstance(request, webob.Request):
            return _build_webob_request_data(request)

    try:
        import werkzeug.wrappers
        import werkzeug.local
    except ImportError:
        pass
    else:
        if isinstance(request, werkzeug.wrappers.Request):
            return _build_werkzeug_request_data(request)
        if isinstance(request, werkzeug.local.LocalProxy):
            actual_request = request._get_current_object()
            return _build_werkzeug_request_data(request)

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
    resp = requests.post(SETTINGS['endpoint'], data=payload, timeout=SETTINGS.get('timeout', 1))
    if resp.status_code != 200:
        log.warning("Got unexpected status code from Ratchet.io api: %s\nResponse:\n%s",
            resp.status_code, resp.text)


def _extract_user_ip(request):
    # some common things passed by load balancers... will need more of these.
    real_ip = request.headers.get('X-Real-Ip')
    if real_ip:
        return real_ip
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for
    return request.remote_addr


