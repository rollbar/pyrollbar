"""
Plugin for Pyramid apps to submit errors to Ratchet.io
"""

import logging
import sys

from pyramid.httpexceptions import WSGIHTTPException
from pyramid.tweens import EXCVIEW

import ratchet

DEFAULT_WEB_BASE = 'https://ratchet.io'


log = logging.getLogger(__name__)


def handle_error(settings, request):
    ratchet.report_exc_info(sys.exc_info(), request)


def parse_settings(settings):
    prefix = 'ratchet.'
    out = {}
    for k, v in settings.iteritems():
        if k.startswith(prefix):
            out[k[len(prefix):]] = v
    return out


def ratchet_tween_factory(pyramid_handler, registry):
    settings = parse_settings(registry.settings)

    whitelist = ()
    blacklist = (WSGIHTTPException,)

    def ratchet_tween(request):
        # for testing out the integration
        try:
            if (settings.get('allow_test', 'true') == 'true' and 
                request.GET.get('pyramid_ratchet_test') == 'true'):
                try:
                    raise Exception("pyramid_ratchet test exception")
                except:
                    handle_error(settings, request)
        except:
            log.exception("Error in pyramid_ratchet_test block")
            
        try:
            response = pyramid_handler(request)
        except whitelist:
            handle_error(settings, request)
            raise
        except blacklist:
            raise
        except:
            handle_error(settings, request)
            raise
        return response

    return ratchet_tween


def patch_debugtoolbar(settings):
    """
    Patches the pyramid_debugtoolbar (if installed) to display a link to the related ratchet item.
    """
    try:
        from pyramid_debugtoolbar import tbtools
    except ImportError:
        return

    ratchet_web_base = settings.get('ratchet.web_base', DEFAULT_WEB_BASE)
    if ratchet_web_base.endswith('/'):
        ratchet_web_base = ratchet_web_base[:-1]
    
    def insert_ratchet_console(request, html):
        # insert after the closing </h1>
        item_uuid = request.environ.get('ratchet.uuid')
        if not item_uuid:
            return html
        
        url = '%s/item/uuid/?uuid=%s' % (ratchet_web_base, item_uuid)
        link = '<a style="color:white;" href="%s">View in Ratchet.io</a>' % url
        new_data = "<h2>Ratchet.io: %s</h2>" % link
        insertion_marker = "</h1>"
        replacement = insertion_marker + new_data
        return html.replace(insertion_marker, replacement, 1)

    # patch tbtools.Traceback.render_full
    old_render_full = tbtools.Traceback.render_full
    def new_render_full(self, request, *args, **kw):
        html = old_render_full(self, request, *args, **kw)
        return insert_ratchet_console(request, html)
    tbtools.Traceback.render_full = new_render_full


def includeme(config):
    """
    Pyramid entry point
    """
    config.add_tween('ratchet.contrib.pyramid.ratchet_tween_factory', under=EXCVIEW)

    # run patch_debugtoolbar, unless they disabled it
    settings = config.registry.settings
    if settings.get('ratchet.patch_debugtoolbar', 'true') == 'true':
        patch_debugtoolbar(settings)
        
    def hook(request, data):
        data['framework'] = 'pyramid'
        
        request.environ['ratchet.uuid'] = data['uuid']
            
    ratchet.BASE_DATA_HOOK = hook
    
    kw = parse_settings(settings)
    
    access_token = kw.pop('access_token')
    environment = kw.pop('environment', 'production')
    
    if kw.get('scrub_fields'):
        kw['scrub_fields'] = set([str.strip(x) for x in kw.get('scrub_fields').split('\n') if x])
    
    ratchet.init(access_token, environment, **kw)

