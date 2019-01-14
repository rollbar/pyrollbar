"""
Integration with Quart
"""

from quart import request
import rollbar


def report_exception(app, exception):
    rollbar.report_exc_info(request=request)


def _hook(request, data):
    data['framework'] = 'quart'

    if request:
        data['context'] = str(request.url_rule)

rollbar.BASE_DATA_HOOK = _hook
