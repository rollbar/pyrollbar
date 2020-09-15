try:
    from django.core.exceptions import ImproperlyConfigured
    from django.http import RawPostDataException
except ImportError:
    ImproperlyConfigured = RuntimeError
    RawPostDataException = Exception

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

    # DRF wraps an original Django HTTP request by their own request and store
    # a wrapped one in _request property. But DRF also can wrap their own
    # request one more time. So we need to set POST on an original request
    # object which is set on the very first DRF request as _request.
    _request = context['request']._request
    while hasattr(_request, '_request'):
        _request = _request._request
    try:
        _request.POST = context['request'].data
    except RawPostDataException:
        # It happens when error is raised by reading request's body.
        pass

    return _exception_handler(exc, context)
