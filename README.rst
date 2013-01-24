pyratchet
=========

pyratchet is a generic library for reporting exceptions and other messages to Ratchet.io_::

    import ratchet, sys
    ratchet.init('YOUR_ACCESS_TOKEN', 'production')  # access_token, environment

    try:
        main_app_loop()
    except IOError:
        ratchet.report_message('Got an IOError in the main loop', 'warning')
    except:
        # catch-all
        ratchet.report_exc_info(sys.exc_info())


Requirements
------------
pyratchet requires:

- Python 2.6 or 2.7
- requests 0.12+
- a Ratchet.io account


Installation
------------
Install using pip::
    
    pip install ratchet


Configuration
-------------
**For generic Python or a non-Django/non-Pyramid framework, follow these instructions:**

Somewhere in your initialization code, call ratchet.init() with your access_token::

    ratchet.init('YOUR_ACCESS_TOKEN_HERE', environment='production')

Other options can be passed as keyword arguments. See the reference below for all options.

**If you are integrating with Django, follow these instructions:**

1. In your ``settings.py``, add ``'ratchet.contrib.django.middleware.RatchetNotifierMiddleware'`` as the last item in ``MIDDLEWARE_CLASSES``::

    MIDDLEWARE_CLASSES = (
        # ... other middleware classes ...
        'ratchet.contrib.django.middleware.RatchetNotifierMiddleware',
    )

2. Add these configuration variables in ``settings.py``::

    RATCHET = {
        'access_token': 'YOUR_ACCESS_TOKEN_HERE',
        'environment': 'development' if DEBUG else 'production',
        'branch': 'master',
        'root': '/absolute/path/to/code/root',
    }

**If you are integrating with Pyramid, follow these instructions:**

1. In your ``ini`` file (e.g. ``production.ini``), add ``ratchet.contrib.pyramid`` to the end of your ``pyramid.includes``::
    
    [app:main]
    pyramid.includes =
        pyramid_debugtoolbar
        ratchet.contrib.pyramid
  
2. Add these ratchet configuration variables::
    
    [app:main]
    ratchet.access_token = YOUR_ACCESS_TOKEN_HERE
    ratchet.environment = production
    ratchet.branch = master
    ratchet.root = %(here)s

Usage
-----
The Django and Pyramid integration will automatically report uncaught exceptions to Ratchet.

Call ``ratchet.report_exc_info()`` to report an exception, or ``ratchet.report_message()`` to report an arbitrary string message. See the docstrings for more info.


Configuration reference
-----------------------

access_token
    Access token from your Ratchet.io project
handler
    One of:

    - blocking -- runs in main thread
    - thread -- spawns a new thread
    - agent -- writes messages to a log file for consumption by ratchet-agent

    **default:** ``thread``
environment
    Environment name. Any string up to 255 chars is OK. For best results, use "production" for your production environment.
root
    Absolute path to the root of your application, not including the final ``/``. 
branch
    Name of the checked-out branch.

    **default:** ``master``
agent.log_file
    If ``handler`` is ``agent``, the path to the log file. Filename must end in ``.ratchet``
endpoint
    URL items are posted to.
    
    **default:** ``https://submit.ratchet.io/api/1/item/``
scrub_fields
    List of field names to scrub out of POST. Values will be replaced with astrickses. If overridiing, make sure to list all fields you want to scrub, not just fields you want to add to the default. Param names are converted to lowercase before comparing against the scrub list.

    **default** ``['passwd', 'password', 'secret', 'confirm_password', 'password_confirmation']``


Developer Resources
-------------------
Get in touch! We'd love to hear what you think and we're happy to help.

- Email us: ``support@ratchet.io``
- IRC: ``#ratchet.io`` on ``irc.freenode.net``
- Want to contribute? Send a pull request at https://github.com/ratchetio/pyratchet


.. _Ratchet.io: http://ratchet.io/
.. _error tracking: http://ratchet.io/
