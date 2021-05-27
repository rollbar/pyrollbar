#!/usr/bin/env python

# This example uses Uvicorn package that must be installed. However, it can be
# replaced with any other ASGI-compliant server.
#
# Optional asynchronous reporting requires HTTPX package to be installed.
#
# NOTE: Starlette middlewares don't allow to collect streamed content like a request body.
#
# Run: python app.py

import rollbar
import uvicorn

from rollbar.contrib.starlette import ReporterMiddleware as RollbarMiddleware
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

# Initialize Rollbar SDK with your server-side ACCESS_TOKEN
rollbar.init(
    'ACCESS_TOKEN',
    environment='staging',
    handler='async',  # For asynchronous reporting use: default, async or httpx
)

# Integrate Rollbar with Starlette application
app = Starlette()
app.add_middleware(RollbarMiddleware)  # should be added as the first middleware


# Verify application runs correctly
#
# $ curl http://localhost:8888
@app.route('/')
async def root(request):
    return PlainTextResponse('hello world')


# Cause an uncaught exception to be sent to Rollbar
# GET query params will be sent to Rollbar and available in the UI
#
# $ curl http://localhost:8888/error?param1=hello&param2=world
async def localfunc(arg1, arg2, arg3):
    # Both local variables and function arguments will be sent to Rollbar
    # and available in the UI
    localvar = 'local variable'
    cause_error_with_local_variables


@app.route('/error')
async def error(request):
    await localfunc('func_arg1', 'func_arg2', 1)
    return PlainTextResponse("You shouldn't be seeing this")


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8888)
