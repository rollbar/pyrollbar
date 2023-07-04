# NOTE: pyrollbar requires both `Flask` and `blinker` packages to be installed first
from flask import Flask
from flask import got_request_exception

import rollbar
import rollbar.contrib.flask


app = Flask(__name__)


with app.app_context():
    rollbar.init('ACCESS_TOKEN', environment='development')
    # send exceptions from `app` to rollbar, using flask's signal system.
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)

@app.route('/')
def root():
    foo()
    return '<html><body>Hello World</body></html>'

if __name__ == '__main__':
    app.run()
