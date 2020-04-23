from threading import Lock
from time import time

_throttle_info = {}     # key: last sent timestamp
_last_optimized = 0
_lock = Lock()



def _get_exception_key(exc_info):
    """ Returns unique string key for exception.

    Key is filename + lineno of exception raise.
    """
    exc_tb = exc_info[2]

    if exc_tb is None:
        return repr(exc_info[1])

    return "{}:{}".format(exc_tb.tb_frame.f_code.co_filename,
                          exc_tb.tb_lineno)


def maybe_throttle_error(exc_info):
    from rollbar import SETTINGS

    key = _get_exception_key(exc_info)
    interval = SETTINGS['error_report_min_interval_seconds']
    return _maybe_throttle_key(key, interval)


def maybe_throttle_message(message):
    from rollbar import SETTINGS

    interval = SETTINGS['message_report_min_interval_seconds']
    return _maybe_throttle_key(message, interval)


def _maybe_throttle_key(key, min_interval):
    if not min_interval:
        return False

    _maybe_optimize_throttle_info()

    with _lock:
        _throttle_info.setdefault(key, 0)
        should_throttle = _throttle_info[key] > time() - min_interval
        if not should_throttle:
            _throttle_info[key] = time()

    return should_throttle


def _maybe_optimize_throttle_info():
    global _last_optimized, _throttle_info
    from rollbar import SETTINGS

    # each gc_interval seconds remove all throttled key infos to prevent
    # memory leak. It may lead to small inaccuracy of sample rate of sent
    # errors, but it is the simpliest way.

    gc_interval = SETTINGS['gc_interval_seconds']

    if _last_optimized < time() - gc_interval:
        with _lock:
            _throttle_info = {}
            _last_optimized = time()
