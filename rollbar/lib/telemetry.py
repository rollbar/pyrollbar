import logging
import threading
import requests
import copy

import rollbar
from rollbar.lib import transforms
from rollbar.lib.transforms.scrub import ScrubTransform


class Queue:
    def __init__(self, size):
        self.size = size
        self.items = []
        self.lock = threading.Lock()

    def put(self, item):
        with self.lock:
            if len(self.items) >= self.size:
                self.items = self.items[1:]
            self.items.append(item)

    def get_items(self):
        with self.lock:
            return self.items

    def clear_items(self):
        with self.lock:
            self.items = []


class TelemetryLogHandler(logging.Handler):
    def __init__(self, formatter=None):
        super(TelemetryLogHandler, self).__init__()
        self.formatter = formatter

    def emit(self, record):
        self.setFormatter(self.formatter)
        msg = {'message': self.format(record)}
        data = {
            'body': msg,
            'source': 'client',
            'timestamp_ms': rollbar.get_current_timestamp(),
            'type': 'log',
            'level': record.levelname,
        }

        rollbar.TELEMETRY_QUEUE.put(data)


def enable_log_telemetry(log_formatter=None):
    logging.getLogger().addHandler(TelemetryLogHandler(log_formatter))


def request(request_function, enable_req_headers, enable_response_headers):
    scrubber = ScrubTransform(suffixes=rollbar.SETTINGS['scrub_fields'], redact_char='*', randomize_len=False)

    def telemetry(*args, **kwargs):

        data = {'level': 'info'}
        data_body = {'status_code': None}
        try:
            response = request_function(*args, **kwargs)
        except:  # noqa: E722
            response = None

        if response is not None:
            data_body['status_code'] = response.status_code
            if response.status_code >= 500:
                data['level'] = 'critical'
            elif response.status_code >= 400:
                data['level'] = 'error'
            if enable_response_headers:
                data_body['response'] = {'headers': transforms.transform(copy.deepcopy(response.headers), scrubber)}
        if enable_req_headers:
            data_body['request_headers'] = transforms.transform(copy.deepcopy(kwargs.get('headers')), scrubber)
        data_body['url'] = args[0]
        data_body['method'] = request_function.__name__.upper()
        data_body['subtype'] = 'http'
        data['body'] = data_body

        data['source'] = 'client'
        data['timestamp_ms'] = rollbar.get_current_timestamp()
        data['type'] = 'network'
        rollbar.TELEMETRY_QUEUE.put(data)

        return response

    return telemetry


def enable_network_telemetry(enable_req_headers, enable_resp_headers):
    requests.get = request(requests.get, enable_req_headers, enable_resp_headers)
    requests.post = request(requests.post, enable_req_headers, enable_resp_headers)
    requests.put = request(requests.put, enable_req_headers, enable_resp_headers)
    requests.patch = request(requests.patch, enable_req_headers, enable_resp_headers)
    requests.delete = request(requests.delete, enable_req_headers, enable_resp_headers)
