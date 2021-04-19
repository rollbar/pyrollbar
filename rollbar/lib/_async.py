import logging

import httpx

import rollbar
from rollbar import DEFAULT_TIMEOUT, SETTINGS
from rollbar.lib import transport, urljoin

log = logging.getLogger(__name__)


async def _post_api_httpx(path, payload_str, access_token=None):
    headers = {'Content-Type': 'application/json'}
    if access_token is not None:
        headers['X-Rollbar-Access-Token'] = access_token
    else:
        headers['X-Rollbar-Access-Token'] = SETTINGS.get('access_token')

    proxy_cfg = {
        'proxy': SETTINGS.get('http_proxy'),
        'proxy_user': SETTINGS.get('http_proxy_user'),
        'proxy_password': SETTINGS.get('http_proxy_password'),
    }
    proxies = transport._get_proxy_cfg(proxy_cfg)

    url = urljoin(SETTINGS['endpoint'], path)
    async with httpx.AsyncClient(
        proxies=proxies, verify=SETTINGS.get('verify_https', True)
    ) as client:
        resp = await client.post(
            url,
            data=payload_str,
            headers=headers,
            timeout=SETTINGS.get('timeout', DEFAULT_TIMEOUT),
        )

    try:
        return rollbar._parse_response(path, access_token, payload_str, resp)
    except Exception as e:
        log.exception('Exception while posting item %r', e)
