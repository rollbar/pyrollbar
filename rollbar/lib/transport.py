import requests
import threading


_local = threading.local()


def _session():
    if hasattr(_local, 'session'):
        return _local.session
    _local.session = requests.Session()
    return _local.session


def post(*args, **kw):
    return _session().post(*args, **kw)


def get(*args, **kw):
    return _session().get(*args, **kw)


__all__ = ['post', 'get']
