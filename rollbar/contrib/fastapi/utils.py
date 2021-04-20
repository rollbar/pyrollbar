import functools
import logging

import fastapi

log = logging.getLogger(__name__)


class FastAPIVersionError(Exception):
    def __init__(self, version, reason=''):
        err_msg = f'FastAPI {version}+ is required'
        if reason:
            err_msg += f' {reason}'

        log.error(err_msg)
        return super().__init__(err_msg)


class fastapi_min_version:
    def __init__(self, min_version):
        self.min_version = min_version

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if fastapi.__version__ < self.min_version:
                raise FastAPIVersionError(
                    '0.41.0', reason=f'to use {func.__name__}() function'
                )

            return func(*args, **kwargs)

        return wrapper
