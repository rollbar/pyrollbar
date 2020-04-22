try:
    from django.core.exceptions import ImproperlyConfigured
except ImportError:
    ImproperlyConfigured = RuntimeError

try:
    from rest_framework.views import exception_handler as _exception_handler
except (ImportError, ImproperlyConfigured):
    _exception_handler = None


def post_exception_handler(exc, context):
    # This is to be used with the Django REST Framework (DRF) as its
    # global exception handler.  It replaces the POST data of the Django
    # request with the parsed data from the DRF.  This is necessary
    # because we cannot read the request data/stream more than once.
    # This will allow us to see the parsed POST params in the rollbar
    # exception log.

    if _exception_handler is None:
        raise ImproperlyConfigured(
            'Could not import rest_framework.views.exception_handler')

    try:
        context['request']._request.POST = context['request'].data
    except Exception:
        pass

    return _exception_handler(exc, context)
