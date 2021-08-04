import logging
import threading
import time

import rollbar


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


TELEMETRY_QUEUE_SIZE = 50
TELEMETRY_QUEUE = Queue(TELEMETRY_QUEUE_SIZE)


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
            'timestamp_ms': get_current_timestamp(),
            'type': 'log',
            'level': record.levelname,
        }

        TELEMETRY_QUEUE.put(data)


def set_log_telemetry(log_formatter=None):
    logging.getLogger().addHandler(TelemetryLogHandler(log_formatter))


def get_current_timestamp():
    return int(time.time())


def request(request_function, enable_req_headers, enable_response_headers):
    def telemetry(*args, **kwargs):
        def clean_headers(headers):
            if not headers:
                return headers
            return {h: '[FILTERED]' if h in rollbar.SETTINGS['scrub_fields'] else headers[h] for h in headers}
            
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
                data_body['response'] = {'headers': clean_headers(response.headers)}
        if enable_req_headers:
            data_body['request_headers'] = clean_headers(kwargs.get('headers'))
        data_body['url'] = args[0]
        data_body['method'] = request_function.__name__
        data_body['subtype'] = 'http'
        data['body'] = data_body

        data['source'] = 'client'
        data['timestamp_ms'] = get_current_timestamp()
        data['type'] = 'network'
        TELEMETRY_QUEUE.put(data)

        return response

    return telemetry
