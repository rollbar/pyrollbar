"""
django-rollbar middleware

To install, add the following in your settings.py:
1. add 'rollbar.contrib.django.middleware.RollbarNotifierMiddleware' to
    a. MIDDLEWARE_CLASSES in Django 1.9 and earlier
    b. MIDDLEWARE in Django 1.10 and up
2. add a section like this:
ROLLBAR = {
    'access_token': 'tokengoeshere',
}

To get more control of middleware and enrich it with custom data:
1. create a 'middleware.py' file on your project (name is up to you)
2. import the rollbar default middleware: 'from rollbar.contrib.django.middleware import RollbarNotifierMiddleware'
3. create your own middleware like this:
class CustomRollbarNotifierMiddleware(RollbarNotifierMiddleware):
    def get_extra_data(self, request, exc):
        ''' May be defined.  Must return a dict or None. Use it to put some custom extra data on rollbar event. '''
        return

    def get_payload_data(self, request, exc):
        ''' May be defined.  Must return a dict or None. Use it to put some custom payload data on rollbar event. '''
        return

4. add 'path.to.your.CustomRollbarNotifierMiddleware' in your settings.py to
    a. MIDDLEWARE_CLASSES in Django 1.9 and earlier
    b. MIDDLEWARE in Django 1.10 and up
5. add a section like this in your settings.py:
ROLLBAR = {
    'access_token': 'tokengoeshere',
}

See README.rst for full installation and configuration instructions.
"""

import logging
import sys

import rollbar

from django.core.exceptions import MiddlewareNotUsed
from django.conf import settings
from django.http import Http404

try:
    from django.urls import resolve
except ImportError:
    from django.core.urlresolvers import resolve

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    from rollbar.contrib.django.utils import MiddlewareMixin

log = logging.getLogger(__name__)


DEFAULTS = {
    'web_base': 'https://rollbar.com',
    'enabled': True,
    'patch_debugview': True,
    'exception_level_filters': [
        (Http404, 'warning')
    ]
}


def _patch_debugview(rollbar_web_base):
    try:
        from django.views import debug
    except ImportError:
        return

    if rollbar_web_base.endswith('/'):
        rollbar_web_base = rollbar_web_base[:-1]

    # modify the TECHNICAL_500_TEMPLATE
    new_data = """
{% if view_in_rollbar_url %}
  <h3 style="margin-bottom:15px;"><a href="{{ view_in_rollbar_url }}" target="_blank">View in Rollbar</a></h3>
{% endif %}
    """

    insert_before = '<table class="meta">'
    replacement = new_data + insert_before

    if hasattr(debug, 'TECHNICAL_500_TEMPLATE'):
        if new_data in debug.TECHNICAL_500_TEMPLATE:
            return
        debug.TECHNICAL_500_TEMPLATE = debug.TECHNICAL_500_TEMPLATE.replace(insert_before, replacement, 1)
    else:
        # patch ExceptionReporter.get_traceback_html if this version of Django is using
        # the file system templates rather than the ones in code
        # This code comes from:
        # https://github.com/django/django/blob/d79cf1e9e2887aa12567c8f27e384195253cb847/django/views/debug.py#L329,L334
        # There are theoretical issues with the code below, for example t.render could throw because
        # t might be None, but this is the code from Django
        from pathlib import Path
        from django.template import Context
        def new_get_traceback_html(exception_reporter):
            """Return HTML version of debug 500 HTTP error page."""
            with Path(debug.CURRENT_DIR, 'templates', 'technical_500.html').open() as fh:
                template_string = fh.read()
                template_string = template_string.replace(insert_before, replacement, 1)
                t = debug.DEBUG_ENGINE.from_string(template_string)
            c = Context(exception_reporter.get_traceback_data(), use_l10n=False)
            return t.render(c)
        debug.ExceptionReporter.get_traceback_html = new_get_traceback_html

    if hasattr(debug.ExceptionReporter, '__rollbar__patched'):
        return

    # patch ExceptionReporter.get_traceback_data
    old_get_traceback_data = debug.ExceptionReporter.get_traceback_data
    def new_get_traceback_data(exception_reporter):
        data = old_get_traceback_data(exception_reporter)
        try:
            item_uuid = exception_reporter.request.META.get('rollbar.uuid')
            if item_uuid:
                url = '%s/item/uuid/?uuid=%s' % (rollbar_web_base, item_uuid)
                data['view_in_rollbar_url'] = url
        except:
            log.exception("Exception while adding view-in-rollbar link to technical_500_template.")
        return data
    debug.ExceptionReporter.get_traceback_data = new_get_traceback_data
    debug.ExceptionReporter.__rollbar__patched = True



class RollbarNotifierMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super(RollbarNotifierMiddleware, self).__init__(get_response)

        self.settings = getattr(settings, 'ROLLBAR', {})
        if not self.settings.get('access_token'):
            raise MiddlewareNotUsed

        if not self._get_setting('enabled'):
            raise MiddlewareNotUsed

        self._ensure_log_handler()

        kw = self.settings.copy()
        access_token = kw.pop('access_token')
        environment = kw.pop('environment', 'development' if settings.DEBUG else 'production')
        kw.setdefault('exception_level_filters', DEFAULTS['exception_level_filters'])

        rollbar.init(access_token, environment, **kw)

        def hook(request, data):
            try:
                # try django 1.5 method for getting url_name
                url_name = request.resolver_match.url_name
            except:
                # fallback to older method
                try:
                    url_name = resolve(request.path_info).url_name
                except:
                    url_name = None

            if url_name:
                data['context'] = url_name

            data['framework'] = 'django'

            if request:
                request.META['rollbar.uuid'] = data['uuid']

        rollbar.BASE_DATA_HOOK = hook

        # monkeypatch debug module
        if self._get_setting('patch_debugview'):
            try:
                _patch_debugview(self._get_setting('web_base'))
            except Exception as e:
                log.error(
                    "Rollbar - unable to monkeypatch debugview to add 'View in Rollbar' link."
                    " To disable, set `ROLLBAR['patch_debugview'] = False` in settings.py."
                    " Exception was: %r", e
                )

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
                if hasattr(default_val, '__call__'):
                    return default_val()
                return default_val
            return default

    def get_extra_data(self, request, exc):
        return

    def get_payload_data(self, request, exc):
        return

    def process_response(self, request, response):
        return response

    def process_exception(self, request, exc):
        rollbar.report_exc_info(
            sys.exc_info(),
            request,
            extra_data=self.get_extra_data(request, exc),
            payload_data=self.get_payload_data(request, exc),
        )
