import bottle, rollbar, sys

to_collect = (
    'body',
    'COOKIES',
    'content_type',
    'content_length',
    'headers',
    'method',
    'path',
    'remote_addr',
    'remote_route',
)
methods = {}
for tc in to_collect:
    methods[tc] = lambda x: x

methods['body'] = lambda x: u''.join(x)
methods['COOKIES'] = lambda x: u'\n'.join([u'%s: %s' % (k, v) for k, v in x.items()])
methods['headers'] = lambda x: u'\n'.join([u'%s: %s' % (k, v) for k, v in x.items()])

class RollbarBottleReporter(object):
    '''
    A Bottle plugin that reports errors to Rollbar
    All args and kwargs are passed to `rollbar.init`
    '''
    name = 'rollbar-bottle-reporter'
    api = 2

    def __init__(self, *args, **kwargs):
        rollbar.init(*args, **kwargs)

    def __call__(self, callback):
        def wrapper(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except Exception, e:
                info = {}
                for k in to_collect:
                    info[k] = methods[k](getattr(bottle.request, k, None))
                info['error'] = u'%s' % e
                rollbar.report_exc_info(sys.exc_info(), extra_data=info)
                raise

        return wrapper
