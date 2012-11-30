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
Somewhere in your initialization code, call ratchet.init() with your access_token::

    ratchet.init('YOUR_ACCESS_TOKEN_HERE', environment='production')

Other options can be passed as keyword arguments. See the reference below for all options.


Usage
-----
Call ``pyratchet.report_exc_info()`` to report an exception, or ``pyratchet.report_message()`` to report an arbitrary string message. See the docstrings for more info.


Configuration reference
-----------------------

access_token
    Access token from your Ratchet.io project
handler
    One of:

    - blocking -- runs in main thread
    - thread -- spawns a new thread

    **default:** ``thread``
environment
    Environment name. Any string up to 255 chars is OK. For best results, use "production" for your production environment.
root
    Absolute path to the root of your application, not including the final ``/``. 
branch
    Name of the checked-out branch.

    **default:** ``master``
endpoint
    URL items are posted to.
    
    **default:** ``https://submit.ratchet.io/api/1/item/``
scrub_fields
    List of field names to scrub out of POST. Values will be replaced with astrickses. If overridiing, make sure to list all fields you want to scrub, not just fields you want to add to the default. Param names are converted to lowercase before comparing against the scrub list.

    **default** ``['passwd', 'password', 'secret']``


Developer Resources
-------------------
Get in touch! We'd love to hear what you think and we're happy to help. You can get involved in several ways:

- Email us: ``support@ratchet.io``
- IRC: ``#ratchet.io`` on ``irc.freenode.net``
- Want to contribute? Send a pull request at https://github.com/ratchetio/pyratchet


.. _Ratchet.io: http://ratchet.io/
.. _error tracking: http://ratchet.io/
