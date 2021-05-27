#!/usr/bin/env python

# This example uses Uvicorn package that must be installed. However, it can be
# replaced with any other ASGI-compliant server.
#
# NOTE: Python 3.6 requires aiocontextvars package to be installed.
#       Optional asynchronous reporting requires HTTPX package to be installed.
#
# Run: python app_logger.py

import logging

import fastapi
import rollbar
import uvicorn

from rollbar.contrib.fastapi import LoggerMiddleware
from rollbar.logger import RollbarHandler

# Initialize Rollbar SDK with your server-side ACCESS_TOKEN
rollbar.init(
    'ACCESS_TOKEN',
    environment='staging',
    handler='async',  # For asynchronous reporting use: default, async or httpx
)

# Set root logger to log DEBUG and above
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Report ERROR and above to Rollbar
rollbar_handler = RollbarHandler()
rollbar_handler.setLevel(logging.ERROR)

# Attach Rollbar handler to the root logger
logger.addHandler(rollbar_handler)

# Integrate Rollbar with FastAPI application
app = fastapi.FastAPI()
app.add_middleware(LoggerMiddleware)  # should be added as the last middleware


# GET query params will be sent to Rollbar and available in the UI
# $ curl http://localhost:8888?param1=hello&param2=world
@app.get('/')
async def read_root():
    # Report log entries
    logger.critical('Critical message sent to Rollbar')
    logger.error('Error message sent to Rollbar')

    # Ignore log entries
    logger.warning('Warning message is not sent to Rollbar')
    logger.info('Info message is not sent to Rollbar')
    logger.debug('Debug message is not sent to Rollbar')

    return {'hello': 'world'}


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8888)
