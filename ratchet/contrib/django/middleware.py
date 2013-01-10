"""
django-ratchet middleware

To install, add the following in your settings.py:
1. add 'ratchet.contrib.django.middleware.RatchetNotifierMiddleware' to MIDDLEWARE_CLASSES 
2. add a section like this:
RATCHET = {
    'access_token': 'tokengoeshere',
}

See README.rst for full installation and configuration instructions.
"""

import logging
import sys

import ratchet

from django.core.exceptions import MiddlewareNotUsed
from django.conf import settings

log = logging.getLogger(__name__)


DEFAULTS = {
    'web_base': 'https://ratchet.io',
    'enabled': True,
    'patch_debugview': True,
}


def _patch_debugview(ratchet_web_base):
    try:
        from django.views import debug
    except ImportError:
        return
    
    if ratchet_web_base.endswith('/'):
        ratchet_web_base = ratchet_web_base[:-1]
    
    # modify the TECHNICAL_500_TEMPLATE
    new_data = """
{% if view_in_ratchet_url %}
  <h3 style="margin-bottom:15px;"><a href="{{ view_in_ratchet_url }}" target="_blank">View in Ratchet.io</a></h3>
{% endif %}
    """
    insert_before = '<table class="meta">'
    replacement = new_data + insert_before
    debug.TECHNICAL_500_TEMPLATE = debug.TECHNICAL_500_TEMPLATE.replace(insert_before, 
        replacement, 1)

    # patch ExceptionReporter.get_traceback_data
    old_get_traceback_data = debug.ExceptionReporter.get_traceback_data
    def new_get_traceback_data(exception_reporter):
        data = old_get_traceback_data(exception_reporter)
        try:
            item_uuid = exception_reporter.request.META.get('ratchet.uuid')
            if item_uuid:
                url = '%s/item/uuid/?uuid=%s' % (ratchet_web_base, item_uuid)
                data['view_in_ratchet_url'] = url
        except:
            log.exception("Exception while adding view-in-ratchet link to technical_500_template.")
        return data
    debug.ExceptionReporter.get_traceback_data = new_get_traceback_data


class RatchetNotifierMiddleware(object):
    def __init__(self):
        self.settings = getattr(settings, 'RATCHET', {})
        if not self.settings.get('access_token'):
            raise MiddlewareNotUsed

        if not self._get_setting('enabled'):
            raise MiddlewareNotUsed
        
        self._ensure_log_handler()
        
        kw = self.settings.copy()
        access_token = kw.pop('access_token')
        environment = kw.pop('environment', 'development' if settings.DEBUG else 'production')
        
        ratchet.init(access_token, environment, **kw)
        
        def hook(request, data):
            data['framework'] = 'django'
            
            request.META['ratchet.uuid'] = data['uuid']
            
        ratchet.BASE_DATA_HOOK = hook
        
        # monkeypatch debug module
        if self._get_setting('patch_debugview'):
            _patch_debugview(self._get_setting('web_base'))

    def _ensure_log_handler(self):
        """
        If there's no log configuration, set up a default handler.
        """
        if log.handlers:
            return
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
    
    def _get_setting(self, name, default=None):
        try:
            return self.settings[name]
        except KeyError:
            if name in DEFAULTS:
                default_val = DEFAULTS[name]
                if callable(default_val):
                    return default_val()
                return default_val
            return default

    def process_response(self, request, response):
        return response

    def process_exception(self, request, exc):
        ratchet.report_exc_info(sys.exc_info(), request)
