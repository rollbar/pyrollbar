import logging

from flask import Flask

import rollbar
from rollbar.logger import RollbarHandler

ACCESS_TOKEN = 'ACCESS_TOKEN'
ENVIRONMENT = 'development'

rollbar.init(ACCESS_TOKEN, ENVIRONMENT)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# report WARNING and above to Rollbar
rollbar_handler = RollbarHandler(history_size=3)
rollbar_handler.setLevel(logging.WARNING)

# gather history for DEBUG+ log messages
rollbar_handler.setHistoryLevel(logging.DEBUG)

# attach the history handler to the root logger
logger.addHandler(rollbar_handler)


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
