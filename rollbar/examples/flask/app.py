import logging

from flask import Flask

import rollbar
from rollbar.logger import RollbarHandler, RollbarRequestAdapter

rollbar.init('92c10f5616944b81a2e6f3c6493a0ec2', 'development')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# report ERROR and above to Rollbar
rollbar_handler = RollbarHandler(history_size=3)
rollbar_handler.setLevel(logging.WARNING)

# attach the history handler to the root logger
logger.addHandler(rollbar_handler)

# wrap the logger to add request data
logger = RollbarRequestAdapter(logger)


app = Flask(__name__)

@app.route('/')
def root():
    logger.info('about to call foo()')
    try:
        foo()
    except:
        logger.exception('Caught exception')

    return '<html><body>Hello World</body></html>'

if __name__ == '__main__':
    app.run()
