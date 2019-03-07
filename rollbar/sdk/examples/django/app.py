import os
import sys

from django.conf import settings


settings.configure(
    DEBUG=True,
    SECRET_KEY='thisisthesecretkey',
    ROOT_URLCONF=__name__,
    ROLLBAR = {
        'access_token': 'POST_SERVER_ITEM_ACCESS_TOKEN',
        'environment': 'development',
        'branch': 'master',
        'root': os.getcwd()
    },
    MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',

        # Rollbar middleware
        'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',
    ),
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
