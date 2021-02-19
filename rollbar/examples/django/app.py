import os
import sys

import django
from django.conf import settings


# use settings compatible with the installed Django version
# v1.10+ requires MIDDLEWARE keyname
# older versions require MIDDLEWARE_CLASSES keyname

ROLLBAR_CONFIG = {
    'access_token': 'POST_SERVER_ITEM_ACCESS_TOKEN',
    'environment': 'development',
    'branch': 'master',
    'root': os.getcwd()
}

MIDDLEWARE_CONFIG = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Rollbar middleware
    'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',
)

if django.VERSION >= (1, 10):
    settings.configure(
        DEBUG=True,
        SECRET_KEY='thisisthesecretkey',
        ROOT_URLCONF=__name__,
        ROLLBAR = ROLLBAR_CONFIG,
        MIDDLEWARE = MIDDLEWARE_CONFIG,
    )
else:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='thisisthesecretkey',
        ROOT_URLCONF=__name__,
        ROLLBAR = ROLLBAR_CONFIG,
        MIDDLEWARE_CLASSES = MIDDLEWARE_CONFIG,
    )

from django.conf.urls import url
from django.http import HttpResponse


def index(request):
    return HttpResponse('Hello World')

def error(request):
    foo()
    return HttpResponse('You shouldn\'t be seeing this')


urlpatterns = (
    url(r'^$', index),
    url(r'^error$', error),
)

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
