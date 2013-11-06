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
    rollbar.report_exc_info(sys.exc_info(), request, payload_data=payload_data)
    
