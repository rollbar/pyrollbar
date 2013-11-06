# Change Log

**0.5.14**
- Fix bug with non-JSON post data in Flask
- Add slightly better integration with Flask. See [rollbar-flask-example](https://github.com/rollbar/rollbar-flask-example) for example usage.

**0.5.13**
- Collect JSON post data in Flask when mimetype is `application/json`

**0.5.12**
- Add sys.argv to server data

**0.5.11**
- Don't report bottle.BaseResponse exceptions in the bottle plugin

**0.5.10**
- Added `code_version` configuration setting
- Added support for bottle request objects

**0.5.9**
- Added a command line interface for reporting messages to Rollbar

**0.5.8**
- Added `allow_logging_basic_config` config flag for compatability with Flask. If using Flask, set to False.

**0.5.7**
- Added `exception_level_filters` configuration setting to customize the level that specific exceptions are reported as.

**0.5.6**
- First argument to `rollbar.report_exc_info()` is now optional. You can now call it with no arguments from within an `except` block, and it will behave is if you had called like `rollbar.report_exc_info(sys.exc_info())`

**0.5.5**
- Support for ignoring exceptions by setting `exc._rollbar_ignore = True`. Such exceptions reported through rollbar.report_exc_info() -- which is used under the hood in the Django and Pyramid middlewares -- will be ignored instead of reported.

**0.5.4**
- Django: catch exceptions when patching the debugview, for better support for django 1.3.

**0.5.3**
- Fixed bug when reporting messages without a request object

**0.5.2**
- Fixed bug where django debug page can get patched twice

**0.5.1**
- Catching possible malformed API responses

**0.5.0**
- Rename to rollbar

**0.4.1**
- report_exc_info() now takes two additional named args: `extra_data` and `payload_data`, like report_message().
- on 429 response (over rate limit), log a warning but don't parse and print an exception.

**0.3.2**
- Added new default scrub fields

**0.3.1**
- Fixed pypi package

**0.3.0**
- Merge django-ratchet and pyramid_ratchet into pyratchet
- Add ability to write to a ratchet-agent log file

**0.2.0**
- Add "person" support

**0.1.14**
- Added payload_data arg to report_message()

**0.1.13**
- Added extra_data arg to report_message()

**0.1.12**
- Use custom JSON encoder to skip objects that can't be encoded.
- Bump default timeout from 1 to 3 seconds.

**0.1.11**
- Sensitive params now scrubbed out of POST. Param name list is customizable via the `scrub_fields` config option.

**0.1.10**
- Add support for Tornado request objects (`tornado.httpserver.HTTPRequest`)

**0.1.9**
- Fix support for Pyramid request objects

**0.1.8**
- Add support for Django request objects

