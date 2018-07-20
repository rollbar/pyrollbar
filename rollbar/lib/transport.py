import requests
import threading


_local = threading.local()


def _session():
    if hasattr(_local, 'session'):
        return _local.session
    _local.session = requests.Session()
    return _local.session


def _get_proxy_cfg(kw):
    proxy = kw.pop('proxy', None)
    proxy_user = kw.pop('proxy_user', None)
    proxy_password = kw.pop('proxy_password', None)
    if proxy and proxy_user and proxy_password:
        return {
            'http': 'http://{}:{}@{}'.format(proxy_user, proxy_password, proxy),
            'https': 'http://{}:{}@{}'.format(proxy_user, proxy_password, proxy),
        }
    elif proxy:
        return {
            'http': 'http://{}'.format(proxy),
            'https': 'http://{}'.format(proxy),
        }


def post(*args, **kw):
    proxies = _get_proxy_cfg(kw)
    return _session().post(*args, proxies=proxies, **kw)


def get(*args, **kw):
    proxies = _get_proxy_cfg(kw)
    return _session().get(*args, proxies=proxies, **kw)


__all__ = ['post', 'get']
