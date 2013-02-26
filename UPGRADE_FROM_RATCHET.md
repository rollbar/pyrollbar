# Upgrading from pyratchet

Execute:

    $ pip uninstall ratchet

Then:

    $ pip install rollbar
    
## Generic Python or a non-Django/non-Pyramid framework

Change your initialization call from `ratchet.init(...)` to `rollbar.init(...)`.

Search your app for all references to `ratchet` and replace them with `rollbar`.

## Pyratchet running with Django

In your `settings.py`:
- change `'ratchet.contrib.django.middleware.RatchetNotifierMiddleware'` to `'rollbar.contrib.django.middleware.RollbarNotifierMiddleware'`
- rename your `RATCHET` configuration dict to `ROLLBAR`

Search your app for all references to `ratchet` and replace them with `rollbar`.

## Pyratchet running with Pyramid

In your `ini` file:
- change the include `ratchet.contrib.pyramid` to `rollbar.contrib.pyramid`
- rename your `ratchet.*` configuration variables to `rollbar.*`

Search your app for all references to `ratchet` and replace them with `rollbar`.