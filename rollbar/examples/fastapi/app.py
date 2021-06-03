#!/usr/bin/env python

# This example uses Uvicorn package that must be installed. However, it can be
# replaced with any other ASGI-compliant server.
#
# Optional asynchronous reporting requires HTTPX package to be installed.
#
# NOTE: This example requires FastAPI v0.41.0+ (see app_middleware.py for alternative).
#
# Run: python app.py

import fastapi
import rollbar
import uvicorn

from rollbar.contrib.fastapi import add_to as rollbar_add_to

# Initialize Rollbar SDK with your server-side ACCESS_TOKEN
rollbar.init(
    'ACCESS_TOKEN',
    environment='staging',
    handler='async',  # For asynchronous reporting use: default, async or httpx
    include_request_body=True,
)

# Integrate Rollbar with FastAPI application before adding routes to the app
app = fastapi.FastAPI()
rollbar_add_to(app)


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


# Cause an uncaught exception to be sent to Rollbar
# POST request body will be sent to Rollbar and available in the UI
#
# curl http://localhost:8888/body -d '{"param1": "hello", "param2": "world"}'
@app.post('/body')
async def read_body():
    cause_error_with_body
    return {'result': "You shouldn't be seeing this"}


# Cause an uncaught exception to be sent to Rollbar
# POST form data will be sent to Rollbar and available in the UI
#
# curl http://localhost:8888/form -F 'param1=hello' -F 'param2=world'
@app.post('/form')
async def read_form():
    cause_error_with_form
    return {'result': "You shouldn't be seeing this"}


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8888)
