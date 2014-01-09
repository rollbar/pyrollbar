"""
Integration with Flask
"""

import sys

from flask import request
import rollbar


def report_exception(app, exception):
    payload_data = {
        'framework': 'Flask',
    }

    if request.url_rule:
        payload_data['context'] = str(request.url_rule)

    rollbar.report_exc_info(sys.exc_info(), request, payload_data=payload_data)
    
