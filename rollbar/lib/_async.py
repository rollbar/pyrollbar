import asyncio
import contextlib
import logging

import httpx

import rollbar
from rollbar import DEFAULT_TIMEOUT
from rollbar.lib import transport, urljoin

log = logging.getLogger(__name__)

ALLOWED_HANDLERS = (
    'async',
    'httpx',
)


async def report_exc_info(
    exc_info=None, request=None, extra_data=None, payload_data=None, level=None, **kw
):
    with async_handler():
        try:
            return await asyncio.create_task(
                _report_exc_info(
                    exc_info, request, extra_data, payload_data, level, **kw
                )
            )
        except Exception as e:
            log.exception('Exception while reporting exc_info to Rollbar. %r', e)


async def _report_exc_info(
    exc_info=None, request=None, extra_data=None, payload_data=None, level=None, **kw
):
    return rollbar.report_exc_info(
        exc_info, request, extra_data, payload_data, level, **kw
    )


async def report_message(
    message, level="error", request=None, extra_data=None, payload_data=None, **kw
):
    with async_handler():
        try:
            return await asyncio.create_task(
                _report_message(message, level, request, extra_data, payload_data)
            )
        except Exception as e:
            log.exception('Exception while reporting message to Rollbar. %r', e)


async def _report_message(
    message, level="error", request=None, extra_data=None, payload_data=None, **kw
):
    return rollbar.report_message(message, level, request, extra_data, payload_data)


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


@contextlib.contextmanager
def async_handler():
    original_handler = rollbar.SETTINGS.get('handler')

    if original_handler not in ALLOWED_HANDLERS:
        log.warn(
            'Running coroutines requires async compatible handler. Switching to default async handler.'
        )
        rollbar.SETTINGS['handler'] = 'async'

    try:
        yield
    finally:
        if original_handler is not None:
            rollbar.SETTINGS['handler'] = original_handler
