"""
django-ratchet context processor

To install, add the following in your settings.py:
1. add 'ratchet.contrib.django.context_processors.ratchet_settings' to TEMPLATE_CONTEXT_PROCESSORS
2. add a section like this:
RATCHET = {
    'client_access_token': 'tokengoeshere',
}
3. you can now access your ratchet settings as ratchet_settings from within your django templates

See README.rst for full installation and configuration instructions.
"""

from django.conf import settings


def ratchet_settings(request):
    """Grabs the ratchet settings to make them available to templates."""
    if not hasattr(settings, 'RATCHET'):
        return {}
    return {'ratchet_settings': settings.RATCHET}
