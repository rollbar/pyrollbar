import rollbar
import rollbar.contrib.fastapi
import uvicorn

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, Response

app = FastAPI()


rollbar.init("ACCESS_TOKEN", environment="development")


@app.exception_handler(Exception)
async def handle_unexpected_exceptions(request: Request, exc: Exception):
    """This won't capture HTTPException."""
    try:
        raise exc
    except Exception:
        rollbar.contrib.fastapi.report_exception(request=request)

    return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/")
async def root(raise_exception: bool = False):
    """Hello world api endpoint.

    Use `?raise_exception=1` to raise an exception.
    """
    if raise_exception:
        raise Exception("Testing exceptions")
    return JSONResponse({"message": "Hello World"})


if __name__ == "__main__":
    uvicorn.run(app)
