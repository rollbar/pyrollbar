pyrollbar
=========

pyrollbar is a generic library for reporting exceptions and other messages to Rollbar_::

    import rollbar, sys
    rollbar.init('YOUR_ACCESS_TOKEN', 'production')  # access_token, environment

    try:
        main_app_loop()
    except IOError:
        rollbar.report_message('Got an IOError in the main loop', 'warning')
    except:
        # catch-all
        rollbar.report_exc_info(sys.exc_info())


Requirements
------------
pyrollbar requires:

- Python 2.6 or 2.7
- requests 0.12+
- a Rollbar account


Installation
------------
Install using pip::
    
    pip install rollbar


Configuration
-------------
**For generic Python or a non-Django/non-Pyramid framework, follow these instructions:**

Somewhere in your initialization code, call rollbar.init() with your access_token::

    rollbar.init('YOUR_ACCESS_TOKEN_HERE', environment='production')

Other options can be passed as keyword arguments. See the reference below for all options.

**If you are integrating with Django, follow these instructions:**

1. In your ``settings.py``, add ``'rollbar.contrib.django.middleware.RollbarNotifierMiddleware'`` as the last item in ``MIDDLEWARE_CLASSES``::

    MIDDLEWARE_CLASSES = (
        # ... other middleware classes ...
        'rollbar.contrib.django.middleware.RollbarNotifierMiddleware',
    )

2. Add these configuration variables in ``settings.py``::

    ROLLBAR = {
        'access_token': 'YOUR_ACCESS_TOKEN_HERE',
        'environment': 'development' if DEBUG else 'production',
        'branch': 'master',
        'root': '/absolute/path/to/code/root',
    }

**If you are integrating with Pyramid, follow these instructions:**

1. In your ``ini`` file (e.g. ``production.ini``), add ``rollbar.contrib.pyramid`` to the end of your ``pyramid.includes``::
    
    [app:main]
    pyramid.includes =
        pyramid_debugtoolbar
        rollbar.contrib.pyramid
  
2. Add these rollbar configuration variables::
    
    [app:main]
    rollbar.access_token = YOUR_ACCESS_TOKEN_HERE
    rollbar.environment = production
    rollbar.branch = master
    rollbar.root = %(here)s

The above will configure rollbar to catch and report all exceptions that occur in your Pyramid app. However, if there are any middleware
applications that wrap your app, Rollbar will not be able to catch exceptions. 

In order to catch exceptions from Pyramid and middleware code, you will need to create a ``pipeline`` where the rollbar middleware wraps your Pyramid app.

- Change your ``ini`` file to use a ``pipeline``::

    From

    [app:main]
    ...

    To

    [pipeline:main]
    pipeline =
        rollbar
        YOUR_APP_NAME

    [app:YOUR_APP_NAME]
    pyramid.includes =
        pyramid_debugtoolbar
        rollbar.contrib.pyramid

    [filter:rollbar]
    access_token = YOUR_ACCESS_TOKEN_HERE
    environment = production
    branch = master
    root = %(here)s


Unfortunately, the rollbar tween and the rollbar filter configurations contains duplicated information. We'll look into fixing this in future versions.

Usage
-----
The Django and Pyramid integration will automatically report uncaught exceptions to Rollbar.

Call ``rollbar.report_exc_info()`` to report an exception, or ``rollbar.report_message()`` to report an arbitrary string message. See the docstrings for more info.


Configuration reference
-----------------------

access_token
    Access token from your Rollbar project
handler
    One of:

    - blocking -- runs in main thread
    - thread -- spawns a new thread
    - agent -- writes messages to a log file for consumption by rollbar-agent

    **default:** ``thread``
environment
    Environment name. Any string up to 255 chars is OK. For best results, use "production" for your production environment.
root
    Absolute path to the root of your application, not including the final ``/``. 
branch
    Name of the checked-out branch.

    **default:** ``master``
agent.log_file
    If ``handler`` is ``agent``, the path to the log file. Filename must end in ``.rollbar``
endpoint
    URL items are posted to.
    
    **default:** ``https://api.rollbar.com/api/1/item/``
scrub_fields
    List of field names to scrub out of POST. Values will be replaced with astrickses. If overridiing, make sure to list all fields you want to scrub, not just fields you want to add to the default. Param names are converted to lowercase before comparing against the scrub list.

    **default** ``['passwd', 'password', 'secret', 'confirm_password', 'password_confirmation']``


Developer Resources
-------------------
Get in touch! We'd love to hear what you think and we're happy to help.

- Email us: ``support@rollbar.com``
- IRC: ``#rollbar.com`` on ``irc.freenode.net``
- Want to contribute? Send a pull request at https://github.com/rollbar/pyrollbar


.. _Rollbar: http://rollbar.com/
.. _error tracking: http://rollbar.com/
