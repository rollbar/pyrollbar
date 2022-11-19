import logging
from concurrent.futures import ThreadPoolExecutor

_pool = None  # type: ThreadPoolExecutor|None

log = logging.getLogger(__name__)


def init_pool(max_workers):
    """
    Creates the thread pool with the max workers.

    :type max_workers: int
    """
    global _pool
    _pool = ThreadPoolExecutor(max_workers)


def submit(worker, payload_str, access_token):
    """
    Submit a new task to the thread pool.

    :type worker: function
    :type payload_str: str
    :type access_token: str
    """
    global _pool
    if _pool is None:
        log.warning('pyrollbar: Thead pool not initialized. Please ensure init_pool() is called prior to submit().')
        return
    _pool.submit(worker, payload_str, access_token)
