#!/usr/bin/env python

# This example uses Uvicorn package that must be installed. However, it can be
# replaced with any other ASGI-compliant server.
#
# NOTE: Python 3.6 requires aiocontextvars package to be installed.
#
# Run: python app_global_request.py

import rollbar
import uvicorn

from rollbar.contrib.starlette import LoggerMiddleware
from starlette.applications import Starlette
from starlette.responses import JSONResponse

# Integrate Rollbar with Starlette application
app = Starlette()
app.add_middleware(LoggerMiddleware)  # should be added as the last middleware


async def get_user_agent():
    # Global access to the current request object
    request = rollbar.get_request()

    user_agent = request.headers['User-Agent']
    return user_agent


# $ curl -i http://localhost:8888
@app.route('/')
async def root(request):
    user_agent = await get_user_agent()
    return JSONResponse({'user-agent': user_agent})


if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8888)
