import logging

log = logging.getLogger(__name__)


class FastAPIVersionError(Exception):
    def __init__(self, version, reason=''):
        err_msg = f'FastAPI {version}+ is required'
        if reason:
            err_msg += f' {reason}'

        log.error(err_msg)
        return super().__init__(err_msg)
