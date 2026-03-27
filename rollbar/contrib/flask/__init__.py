"""
Integration with Flask
"""

from flask import request, got_request_exception, Flask
import rollbar
from rollbar.lib.session import reset_current_session, set_current_session


def report_exception(app, exception):
    rollbar.report_exc_info(request=request)


def _hook(request, data):
    data['framework'] = 'flask'

    if request:
        data['context'] = str(request.url_rule)

rollbar.BASE_DATA_HOOK = _hook


def init(app: Flask, access_token, environment='production', scrub_fields=None, url_fields=None, **kw):
    """
    Initializes the Rollbar Flask integration.
    """
    with app.app_context():
        rollbar.init(
            access_token=access_token,
            environment=environment,
            scrub_fields=scrub_fields,
            url_fields=url_fields,
            **kw,
        )
        # send exceptions from `app` to rollbar, using flask's signal system.
        got_request_exception.connect(report_exception, app)

    @app.before_request
    def before_request():
        set_current_session(dict(request.headers))

    @app.teardown_request
    def teardown_request(exception):
        reset_current_session()