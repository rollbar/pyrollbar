pyratchet
=========

pyratchet is a generic library for reporting exceptions and other messages to Ratchet.io_.


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


Contributing
------------

Contributions are welcome. The project is hosted on github at http://github.com/ratchetio/pyratchet


Additional Help
---------------
If you have any questions, feedback, etc., drop me a line at brian@ratchet.io


.. _Ratchet.io: http://ratchet.io/
.. _error tracking: http://ratchet.io/
