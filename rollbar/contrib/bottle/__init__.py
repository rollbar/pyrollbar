import bottle, rollbar, sys

class RollbarBottleReporter(object):
    '''
    A Bottle plugin that reports errors to Rollbar
    All args and kwargs are passed to `rollbar.init`
    '''
    name = 'rollbar-bottle-reporter'
    api = 2

    def __init__(self, *args, **kwargs):
        if 'exception_level_filters' in kwargs:
            kwargs['exception_level_filters'].append((bottle.BaseResponse, 'ignored'))
        else:
            kwargs['exception_level_filters'] = [(bottle.BaseResponse, 'ignored')]

        rollbar.init(*args, **kwargs)

    def __call__(self, callback):
        def wrapper(*args, **kwargs):
            try:
                return callback(*args, **kwargs)
            except Exception, e:
                payload_data = None
                try:
                    route = bottle.request['bottle.route']
                    payload_data = {'context': route.name or route.rule}
                except:
                    pass

                rollbar.report_exc_info(sys.exc_info(), request=bottle.request, payload_data=payload_data)
                raise

        return wrapper


