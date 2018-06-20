Rollbar notifier for Python |Build Status|
==========================================

Python notifier for reporting exceptions, errors, and log messages to
`Rollbar <https://rollbar.com>`__.

Quick start
-----------

Install using pip:

.. code:: bash

    pip install rollbar

.. code:: python

    import rollbar
    rollbar.init('POST_SERVER_ITEM_ACCESS_TOKEN', 'production')  # access_token, environment

    try:
        main_app_loop()
    except IOError:
        rollbar.report_message('Got an IOError in the main loop', 'warning')
    except:
        # catch-all
        rollbar.report_exc_info()
        # equivalent to rollbar.report_exc_info(sys.exc_info())

Requirements
------------

-  Python 2.7, 3.3, 3.4, or 3.5
-  requests 0.12+
-  A Rollbar account

Configuration
-------------

Django
~~~~~~

In your ``settings.py``, add
``'rollbar.contrib.django.middleware.RollbarNotifierMiddleware'`` as the
last item in

-  ``MIDDLEWARE_CLASSES`` in Django 1.9 and earlier:

``python   MIDDLEWARE_CLASSES = [       # ... other middleware classes ...       'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',   ]``

-  ``MIDDLEWARE`` in Django 1.10 and up:

``python   MIDDLEWARE = [       # ... other middleware classes ...       'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',   ]``

Add these configuration variables in ``settings.py``:

.. code:: python

    ROLLBAR = {
        'access_token': 'POST_SERVER_ITEM_ACCESS_TOKEN',
        'environment': 'development' if DEBUG else 'production',
        'branch': 'master',
        'root': '/absolute/path/to/code/root',
    }

Be sure to replace ``POST_SERVER_ITEM_ACCESS_TOKEN`` with your project's
``post_server_item`` access token, which you can find in the Rollbar.com
interface.

Check out the `Django
example <https://github.com/rollbar/pyrollbar/tree/master/rollbar/examples/django>`__.

If you'd like to be able to use a Django ``LOGGING`` handler that could
catch errors that happen outside of the middleware and ship them to
Rollbar, such as in celery job queue tasks that run in the background
separate from web requests, do the following:

Add this to the ``handlers`` key:

::

        'rollbar': {
            'filters': ['require_debug_false'],
            'access_token': 'POST_SERVER_ITEM_ACCESS_TOKEN',
            'environment': 'production',
            'class': 'rollbar.logger.RollbarHandler'
        },

Then add the handler to the ``loggers`` key values where you want it to
fire off.

::

        'myappwithtasks': {
            'handlers': ['console', 'logfile', 'rollbar'],
            'level': 'DEBUG',
            'propagate': True,
        },

Pyramid
~~~~~~~

In your ``ini`` file (e.g. ``production.ini``), add
``rollbar.contrib.pyramid`` to the end of your ``pyramid.includes``:

.. code:: ini

    [app:main]
    pyramid.includes =
        pyramid_debugtoolbar
        rollbar.contrib.pyramid

And add these rollbar configuration variables:

.. code:: ini

    [app:main]
    rollbar.access_token = POST_SERVER_ITEM_ACCESS_TOKEN
    rollbar.environment = production
    rollbar.branch = master
    rollbar.root = %(here)s

Be sure to replace ``POST_SERVER_ITEM_ACCESS_TOKEN`` with your project's
``post_server_item`` access token, which you can find in the Rollbar.com
interface.

The above will configure Rollbar to catch and report all exceptions that
occur inside your Pyramid app. However, in order to catch exceptions in
middlewares or in Pyramid itself, you will also need to wrap your app
inside a ``pipeline`` with Rollbar as a ``filter``.

To do this, first change your ``ini`` file to use a ``pipeline``. Change
this:

.. code:: ini

    [app:main]
    #...

To:

.. code:: ini

    [pipeline:main]
    pipeline =
        rollbar
        YOUR_APP_NAME

    [app:YOUR_APP_NAME]
    pyramid.includes =
        pyramid_debugtoolbar
        rollbar.contrib.pyramid

    rollbar.access_token = POST_SERVER_ITEM_ACCESS_TOKEN
    rollbar.environment = production
    rollbar.branch = master
    rollbar.root = %(here)s

    [filter:rollbar]
    use = egg:rollbar#pyramid
    access_token = POST_SERVER_ITEM_ACCESS_TOKEN
    environment = production
    branch = master
    root = %(here)s

Note that the access\_token, environment, and other Rollbar config
params do need to be present in both the ``app`` section and the
``filter`` section.

Additionally, note that because Pyramid uses INI files for
configuration, any changes to nested settings, like the ``locals``
dictionary, will need to be handled in code.

Flask
~~~~~

Check out
`rollbar-flask-example <https://github.com/rollbar/rollbar-flask-example>`__.

Be sure to add the required ``blinker`` dependency! See
``requirements.txt`` in the example repo for how.

Bottle
~~~~~~

Import the plugin and install! Can be installed globally or on a per
route basis.

.. code:: python

    import bottle
    from rollbar.contrib.bottle import RollbarBottleReporter

    rbr = RollbarBottleReporter(access_token='POST_SERVER_ITEM_ACCESS_TOKEN', environment='production') #setup rollbar

    bottle.install(rbr) #install globally

    @bottle.get('/')
    def raise_error():
      '''
      When navigating to /, we'll get a regular 500 page from bottle,
      as well as have the error below listed on Rollbar.
      '''
      raise Exception('Hello, Rollbar!')

    if __name__ == '__main__':
        bottle.run(host='localhost', port=8080)

Be sure to replace ``POST_SERVER_ITEM_ACCESS_TOKEN`` with your project's
``post_server_item`` access token, which you can find in the Rollbar.com
interface.

Twisted
~~~~~~~

Check out the `Twisted
example <https://github.com/rollbar/pyrollbar/tree/master/rollbar/examples/twisted>`__.

AWS Lambda
~~~~~~~~~~

The biggest issue with the Lambda execution environment is that as soon
as you return from your handler function, any work executing in other
threads will stop executing as the process is frozen. This is true also
of any child processes that one may spawn. Furthermore, the Lambda
environment implements multithreading via a hypervisor on a single CPU
core. Therefore, using separate threads to do additional work will not
necessarily lead to better performance.

In order to ensure that the Rollbar library works correctly, meaning
that items are transmitted to the Rollbar API, one must not return from
the main handler function before all of this work completes. In order to
ensure this, one can either use the ``blocking`` handler by specifying
this value in the configuration,

.. code:: python

    rollbar.init(token, environment='production', handler='blocking')

or use the Rollbar function wait to delay the return from your function
until all Rollbar threads have finished. Note that we use threads for
the handler if otherwise unspecified, therefore you must use wait if you
do not set the handler.

``wait`` is a function which takes an optional function as an argument.
It waits for all currently running Rollbar created threads to stop
processing, meaning it waits for any items to be sent over the network,
then it returns the result of calling the function passed as an argument
or ``None`` if function was given. Hence, one can use it via

.. code:: python

    def lambda_handler(event, context):
        try:
            result = ...
            return rollbar.wait(lambda: result)
        except:
            rollbar.report_exc_info()
            rollbar.wait()
            raise

We provide a decorator for your handler functions which takes care of
calling wait properly as well as catching any exceptions, namely
``rollbar.lambda_function``:

.. code:: python

    import os
    import rollbar

    token = os.getenv('ROLLBAR_KEY', 'missing_api_key')
    rollbar.init(token, 'production')

    @rollbar.lambda_function
    def lambda_handler(event, context):
        return some_other_function('Hello from Lambda')

Other
~~~~~

For generic Python or a non-Django/non-Pyramid framework just initialize
the Rollbar library with your access token and environment.

.. code:: python

    rollbar.init('POST_SERVER_ITEM_ACCESS_TOKEN', environment='production', **other_config_params)

Other options can be passed as keyword arguments. See the reference
below for all options.

Command-line usage
~~~~~~~~~~~~~~~~~~

pyrollbar comes with a command-line tool that can be used with other
UNIX utilities to create an ad-hoc monitoring solution.

e.g. Report all 5xx haproxy requests as ``warning``

.. code:: bash

    tail -f /var/log/haproxy.log | awk '{print $11,$0}' | grep '^5' | awk '{$1="";print "warning",$0}' | rollbar -t POST_SERVER_ITEM_ACCESS_TOKEN -e production -v

e.g. Test an access token

.. code:: bash

    rollbar -t POST_SERVER_ITEM_ACCESS_TOKEN -e test debug testing access token

Reference
^^^^^^^^^

::

    $ rollbar --help
    Usage: rollbar [options]

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -t ACCESS_TOKEN, --access_token=ACCESS_TOKEN
                            You project's access token from rollbar.com.
      -e ENVIRONMENT, --environment=ENVIRONMENT
                            The environment to report errors and messages to.
      -u ENDPOINT_URL, --url=ENDPOINT_URL
                            The Rollbar API endpoint url to send data to.
      -m HANDLER, --handler=HANDLER
                            The method in which to report errors.
      -v, --verbose         Print verbose output.

Usage
-----

The Django, Pyramid, Flask, and Bottle integrations will automatically
report uncaught exceptions to Rollbar.

Exceptions
~~~~~~~~~~

To report a caught exception to Rollbar, use
``rollbar.report_exc_info()``:

.. code:: python

    try:
        do_something()
    except:
        rollbar.report_exc_info(sys.exc_info())
        # or if you have a webob-like request object, pass that as well:
        # rollbar.report_exc_info(sys.exc_info(), request)

Logging
~~~~~~~

You can also send any other log messages you want, using
``rollbar.report_message()``:

.. code:: python

    try:
        do_something()
    except IOError:
        rollbar.report_message('Got an IOError while trying to do_something()', 'warning')
        # report_message() also accepts a request object:
        #rollbar.report_message('message here', 'warning', request)

Examples
~~~~~~~~

Here's a full example, integrating into a simple Gevent app.

.. code:: python

    """
    Sample Gevent application with Rollbar integration.
    """
    import sys
    import logging

    from gevent.pywsgi import WSGIServer
    import rollbar
    import webob

    # configure logging so that rollbar's log messages will appear
    logging.basicConfig()

    def application(environ, start_response):
        request = webob.Request(environ)
        status = '200 OK'
        headers = [('Content-Type', 'text/html')]
        start_response(status, headers)

        yield '<p>Hello world</p>'

        # extra fields we'd like to send along to rollbar (optional)
        extra_data = {'datacenter': 'us1', 'app' : {'version': '1.1'}}

        try:
            # will raise a NameError about 'bar' not being defined
            foo = bar
        except:
            # report full exception info
            rollbar.report_exc_info(sys.exc_info(), request, extra_data=extra_data)

            # and/or, just send a string message with a level
            rollbar.report_message("Here's a message", 'info', request, extra_data=extra_data)

            yield '<p>Caught an exception</p>'

    # initialize rollbar with an access token and environment name
    rollbar.init('POST_SERVER_ITEM_ACCESS_TOKEN', 'development')

    # now start the wsgi server
    WSGIServer(('', 8000), application).serve_forever()

Configuration reference
-----------------------

access\_token
  Access token from your Rollbar project

agent.log\_file
  If ``handler`` is ``agent``, the path to the log file. Filename must end in ``.rollbar``

branch
  Name of the checked-out branch.

  Default: ``master``

code\_version
  A string describing the current code revision/version (i.e. a git sha). Max 40 characters.

  Default: ``None``

enabled
  Controls whether or not Rollbar will report any data

  Default: ``True``

endpoint
  URL items are posted to.

  Default: ``https://api.rollbar.com/api/1/item/``

environment
  Environment name. Any string up to 255 chars is OK. For best results, use "production" for your production environment.

exception\_level\_filters

  List of tuples in the form ``(class, level)`` where ``class`` is an Exception class you want to always filter to the respective ``level``. Any subclasses of the given ``class`` will also be matched.

  Valid levels: ``'critical'``, ``'error'``, ``'warning'``, ``'info'``, ``'debug'`` and ``'ignored'``.

  Use ``'ignored'`` if you want an Exception (sub)class to never be reported to Rollbar.

  Any exceptions not found in this configuration setting will default to ``'error'``.

  Django ``settings.py`` example (and Django default):

  .. code:: python

      from django.http import Http404

      ROLLBAR = {
          ...
          'exception_level_filters': [
              (Http404, 'warning')
          ]
      }

  In a Pyramid ``ini`` file, define each tuple as an individual whitespace delimited line, for example:

  ::

      rollbar.exception_level_filters =
          pyramid.exceptions.ConfigurationError critical
          #...

handler
  The method for reporting rollbar items to api.rollbar.com

  One of:

  -  blocking -- runs in main thread
  -  thread -- spawns a new thread
  -  agent -- writes messages to a log file for consumption by
     rollbar-agent
  -  tornado -- uses the Tornado async library to send the payload
  -  gae -- uses the Google AppEngineFetch library to send the payload
  -  twisted -- uses the Twisted event-driven networking library to send
     the payload

  Default: ``thread``

locals
  Configuration for collecting local variables. A dictionary:

  enabled
    If ``True``, variable values will be collected for stack traces. Default ``True``.

  safe\_repr
    If ``True``, non-built-in objects will be serialized into just their class name. If ``False`` ``repr(obj)`` will be used for serialization. Default ``True``.

sizes
  Dictionary of configuration describing the max size to repr() for each type.

  maxdict
    Default 10

  maxarray
    Default 10

  maxlist
    Default 10

  maxtuple
    Default 10

  maxset
    Default 10

  maxfrozenset
    Default 10

  maxdeque
    Default 10

  maxstring
    Default 100

  maxlong
    Default 40

  maxother
    Default 100

whitelisted\_types
  A list of ``type`` objects, (e.g. ``type(my_class_instance)`` or ``MyClass``) that will be serialized using ``repr()``. Default ``[]``

scrub\_varargs
  If ``True``, variable argument values will be scrubbed. Default ``True``.

root
  Absolute path to the root of your application, not including the final ``/``.

scrub\_fields
  List of sensitive field names to scrub out of request params and locals. Values will be replaced with asterisks. If overriding, make sure to list all fields you want to scrub, not just fields you want to add to the default. Param names are converted to lowercase before comparing against the scrub list.

  Default: ``['pw', 'passwd', 'password', 'secret', 'confirm_password', 'confirmPassword', 'password_confirmation', 'passwordConfirmation', 'access_token', 'accessToken', 'auth', 'authentication']``

timeout
  Timeout for any HTTP requests made to the Rollbar API (in seconds).

  Default: ``3``

allow\_logging\_basic\_config
  When True, ``logging.basicConfig()`` will be called to set up the logging system. Set to False to skip this call. If using Flask, you'll want to set to ``False``. If using Pyramid or Django, ``True`` should be fine.

  Default: ``True``

url\_fields
  List of fields treated as URLs and scrubbed. Default ``['url', 'link', 'href']``

verify\_https
  If ``True``, network requests will fail unless encountering a valid certificate. Default ``True``.

shortener\_keys
  A list of key prefixes (as tuple) to apply our shortener transform to.

  Added to built-in list:

  ::

      [
          ('body', 'request', 'POST'),
          ('body', 'request', 'json')
      ]

  If ``locals.enabled`` is ``True``, extra keys are also automatically added:

  ::

      [
          ('body', 'trace', 'frames', '*', 'code'),
          ('body', 'trace', 'frames', '*', 'args', '*'),
          ('body', 'trace', 'frames', '*', 'kwargs', '*'),
          ('body', 'trace', 'frames', '*', 'locals', '*')
      ]

  Default: ``[]``


suppress\_reinit\_warning
  If ``True``, suppresses the warning normally shown when ``rollbar.init()`` is called multiple times. Default ``False``.


capture\_ip
  If equal to `True`, we will attempt to capture the full client IP address from a request.

  If equal to the string `anonymize`, we will capture the client IP address, but then semi-anonymize it by masking out the least significant bits.

  If equal to `False`, we will not capture the client IP address from a request.


capture\_email
  If set to `True`, we will attempt to enrich person data with an email address if available.

  By default this is set to `False`, which implies we will not include an email address with person data.


capture\_username
  If set to `True`, we will attempt to enrich person data with a username if available.

  By default this is set to `False`, which implies we will not include a username with person data.



Help / Support
--------------

If you run into any issues, please email us at support@rollbar.com

You can also find us in IRC: `#rollbar on
chat.freenode.net <irc://chat.freenode.net/rollbar>`__

For bug reports, please `open an issue on
GitHub <https://github.com/rollbar/pyrollbar/issues/new>`__.

Contributing
------------

1. Fork it
2. Create your feature branch (``git checkout -b my-new-feature``).
3. Commit your changes (``git commit -am 'Added some feature'``)
4. Push to the branch (``git push origin my-new-feature``)
5. Create new Pull Request

Tests are in ``rollbar/test``. To run the tests:
``python setup.py test``

.. |Build Status| image:: https://api.travis-ci.org/rollbar/pyrollbar.png?branch=v0.14.1
   :target: https://travis-ci.org/rollbar/pyrollbar
