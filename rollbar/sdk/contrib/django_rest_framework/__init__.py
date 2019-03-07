try:
    from django.core.exceptions import ImproperlyConfigured
except ImportError:
    RestFrameworkExceptionHandler = None
else:
    try:
        from rest_framework.views import exception_handler as RestFrameworkExceptionHandler
    except (ImportError, ImproperlyConfigured):
        RestFrameworkExceptionHandler = None

    del ImproperlyConfigured


def post_exception_handler(exc, context):
    # This is to be used with the Django REST Framework (DRF) as its
    # global exception handler.  It replaces the POST data of the Django
    # request with the parsed data from the DRF.  This is necessary
    # because we cannot read the request data/stream more than once.
    # This will allow us to see the parsed POST params in the rollbar
    # exception log.
    context['request']._request.POST = context['request'].data
    return RestFrameworkExceptionHandler(exc, context)
