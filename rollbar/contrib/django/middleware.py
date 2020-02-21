r"""
django-rollbar middleware

There are two options for installing the Rollbar middleware. Both options
require modifying your settings.py file.

The first option is to use
'rollbar.contrib.django.middleware.RollbarNotifierMiddleware' which will
report all exceptions to Rollbar including 404s. This middlware should be
placed as the last item in your middleware list which is:
    * MIDDLEWARE_CLASSES in Django 1.9 and earlier
    * MIDDLEWARE in Django 1.10 and up

The other option is two use the two separate middlewares:
    * 'rollbar.contrib.django.middleware.RollbarNotifierMiddlewareExcluding404'
    * 'rollbar.contrib.django.middleware.RollbarNotifierMiddlewareOnly404'
The Excluding404 middleware should be placed as the last item in your middleware
list, and the Only404 middleware should be placed as the first item in your
middleware list. This allows 404s to be processed by your other middlewares
before sendind an item to Rollbar. Therefore if you handle the 404 differently
in a way that returns a response early you won't end up with a Rollbar item.

Regardless of which method you use, you also should add a section to settings.py
like this:

ROLLBAR = {
    'access_token': 'tokengoeshere',
}

This can be used for passing configuration options to Rollbar. Additionally,
you can use the key 'ignorable_404_urls' to set an iterable of regular expression
patterns to use to determine whether a 404 exception should be ignored based
on the full url path for the request. For example,

import re
ROLLBAR = {
    'access_token': 'YOUR_TOKEN',
    'ignorable_404_urls': (
        re.compile(r'/index\.php'),
        re.compile('/foobar'),
    ),
}

To get more control of middleware and enrich it with custom data
you can subclass any of the middleware classes described above
and optionally override the methods:
    def get_extra_data(self, request, exc):
        ''' May be defined.  Must return a dict or None. Use it to put some custom extra data on rollbar event. '''
        return

    def get_payload_data(self, request, exc):
        ''' May be defined.  Must return a dict or None. Use it to put some custom payload data on rollbar event. '''
        return
You would then insert your custom subclass into your middleware
configuration in the same place as the base class as described above.
For example:

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
from six import reraise

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



def _should_ignore_404(url):
    url_patterns = getattr(settings, 'ROLLBAR', {}).get('ignorable_404_urls', ())
    return any(p.search(url) for p in url_patterns)


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

        # ignorable_404_urls is only relevant for this middleware not as an argument to init
        kw.pop('ignorable_404_urls', None)

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

            if request and hasattr(request, 'META'):
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
        if isinstance(exc, Http404) and _should_ignore_404(request.get_full_path()):
            return
        rollbar.report_exc_info(
            sys.exc_info(),
            request,
            extra_data=self.get_extra_data(request, exc),
            payload_data=self.get_payload_data(request, exc),
        )


class RollbarNotifierMiddlewareOnly404(MiddlewareMixin):
    def get_extra_data(self, request, exc):
        return

    def get_payload_data(self, request, exc):
        return

    def process_response(self, request, response):
        if response.status_code != 404:
            return response

        if _should_ignore_404(request.get_full_path()):
            return response

        try:
            if hasattr(request, '_rollbar_notifier_original_http404_exc_info'):
                exc_type, exc_value, exc_traceback = request._rollbar_notifier_original_http404_exc_info
                reraise(exc_type, exc_value, exc_traceback)
            else:
                raise Http404()
        except Exception as exc:
            rollbar.report_exc_info(
                sys.exc_info(),
                request,
                extra_data=self.get_extra_data(request, exc),
                payload_data=self.get_payload_data(request, exc),
            )
        return response


class RollbarNotifierMiddlewareExcluding404(RollbarNotifierMiddleware):
    def process_exception(self, request, exc):
        if isinstance(exc, Http404):
            request._rollbar_notifier_original_http404_exc_info = sys.exc_info()
        else:
            super(RollbarNotifierMiddlewareExcluding404, self).process_exception(request, exc)
