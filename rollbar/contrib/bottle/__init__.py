import bottle, rollbar, sys

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
                rollbar.report_exc_info(sys.exc_info(), request=bottle.request)
                raise

        return wrapper
