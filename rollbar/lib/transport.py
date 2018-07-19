import requests
import threading


_local = threading.local()


def _session():
    if hasattr(_local, 'session'):
        return _local.session
    _local.session = requests.Session()
    return _local.session


def _get_proxy_cfg(proxy):
    if proxy:
        return {
            'http': proxy,
        }


def post(*args, proxy=None, **kw):

    return _session().post(*args, proxies=_get_proxy_cfg(proxy), **kw)


def get(*args, proxy=None, **kw):
    return _session().get(*args, proxies=_get_proxy_cfg(proxy), **kw)


__all__ = ['post', 'get']
