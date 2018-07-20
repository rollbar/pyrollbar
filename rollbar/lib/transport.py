import requests
import threading


_local = threading.local()


def _session():
    if hasattr(_local, 'session'):
        return _local.session
    _local.session = requests.Session()
    return _local.session


def _get_proxy_cfg(proxy=None, proxy_user=None, proxy_password=None):
    if proxy and proxy_user and proxy_password:
        return {
            'http': 'http://{}:{}@{}'.format(proxy_user, proxy_password, proxy),
        }
    elif proxy:
        return {
            'http': 'http://{}'.format(proxy),
        }


def post(*args, proxy=None, proxy_user=None, proxy_password=None, **kw):

    return _session().post(*args, proxies=_get_proxy_cfg(proxy, proxy_user, proxy_password), **kw)


def get(*args, proxy=None, proxy_user=None, proxy_password=None, **kw):
    return _session().get(*args, proxies=_get_proxy_cfg(proxy, proxy_user, proxy_password), **kw)


__all__ = ['post', 'get']
