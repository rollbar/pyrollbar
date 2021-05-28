#!/usr/bin/env python

# This example uses Uvicorn package that must be installed. However, it can be
# replaced with any other ASGI-compliant server.
#
# Optional asynchronous reporting requires HTTPX package to be installed.
#
# NOTE: FastAPI middlewares don't allow to collect streamed content like a request body.
#       You may consider to use routing integration instead (see app.py example).
#
# Run: python app_middleware.py

import fastapi
import rollbar
import uvicorn

from rollbar.contrib.fastapi import ReporterMiddleware as RollbarMiddleware

# Initialize Rollbar SDK with your server-side ACCESS_TOKEN
rollbar.init(
    'ACCESS_TOKEN',
    environment='staging',
    handler='async',  # For asynchronous reporting use: default, async or httpx
)

# Integrate Rollbar with FastAPI application
app = fastapi.FastAPI()
app.add_middleware(RollbarMiddleware)  # should be added as the first middleware


# Verify application runs correctly
#
# $ curl http://localhost:8888
@app.get('/')
async def read_root():
    return {'hello': 'world'}


# Cause an uncaught exception to be sent to Rollbar
# GET query params will be sent to Rollbar and available in the UI
#
# $ curl http://localhost:8888/error?param1=hello&param2=world
async def localfunc(arg1, arg2, arg3):
    # Both local variables and function arguments will be sent to Rollbar
    # and available in the UI
    localvar = 'local variable'
    cause_error_with_local_variables


@app.get('/error')
async def read_error():
    await localfunc('func_arg1', 'func_arg2', 1)
    return {'result': "You shouldn't be seeing this"}


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8888)
