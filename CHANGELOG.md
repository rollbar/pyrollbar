# Change Log

The change log is also available on the [GitHub Releases Page](https://github.com/rollbar/pyrollbar/releases).

**1.3.0**

- Added support for classes to define the method `__rollbar_repr__` to control how objects are serialized by @danielmorell in [#479](https://github.com/rollbar/pyrollbar/pull/479)
- Added support for Python 3.13 by @danielmorell in [#477](https://github.com/rollbar/pyrollbar/pull/477)
- Removed support for Python 3.6 by @danielmorell in [#480](https://github.com/rollbar/pyrollbar/pull/480)
- Updated framework versions tested against by @danielmorell in [#480](https://github.com/rollbar/pyrollbar/pull/480)

**1.2.0**

- Added support for custom payload transforms by @danielmorell in [#470](https://github.com/rollbar/pyrollbar/pull/470)
- Added custom data to the message body by @waltjones in [#473](https://github.com/rollbar/pyrollbar/pull/473)
- Added support for host override setting by @danielmorell in [#468](https://github.com/rollbar/pyrollbar/pull/468)
- Fixed `RollbarHandler` reconfigures root logger by @ilkecan in [#463](https://github.com/rollbar/pyrollbar/pull/463)
- Fixed `include_request_body` setting not checked for various frameworks by @danielmorell in [#469](https://github.com/rollbar/pyrollbar/pull/469)
- Fixed `namedtuple` fields not being scrubbed by @danielmorell in [#474](https://github.com/rollbar/pyrollbar/pull/474)

**1.1.2**

Fixed build missing entrypoints for pyramid and cli in [#471](https://github.com/rollbar/pyrollbar/pull/471)

**1.1.1**

Fixed #465 httpx 0.28.0 not compatible with pyrollbar by @danielmorell in [#466](https://github.com/rollbar/pyrollbar/pull/466)

**1.1.0**

- Updated supported/tested frameworks and modernized tests and packaging by @danielmorell in [#455](https://github.com/rollbar/pyrollbar/pull/455)
- Fixed #398 FastAPI integration fails if docs are disabled by @danielmorell in [#459](https://github.com/rollbar/pyrollbar/pull/459)
- Support `pathlib.Path()` objects by @singingwolfboy in [$450](https://github.com/rollbar/pyrollbar/pull/450)
- Added support for Python 3.12 by @danielmorell in [#460](https://github.com/rollbar/pyrollbar/pull/460)
- Changed the `ShortenerTransform` to use breadth first traversal by @danielmorell in [#461](https://github.com/rollbar/pyrollbar/pull/461)
- Fixed shortener multi level shortening by @danielmorell and @pawelsz-rb. See [#449](https://github.com/rollbar/pyrollbar/pull/449)

**1.1.0-beta**

- Updated supported/tested frameworks and modernized tests and packaging by @danielmorell in [#455](https://github.com/rollbar/pyrollbar/pull/455)
- Fixed #398 FastAPI integration fails if docs are disabled by @danielmorell in [#459](https://github.com/rollbar/pyrollbar/pull/459)
- Support `pathlib.Path()` objects by @singingwolfboy in [$450](https://github.com/rollbar/pyrollbar/pull/450)
- Added support for Python 3.12 by @danielmorell in [#460](https://github.com/rollbar/pyrollbar/pull/460)
- Changed the `ShortenerTransform` to use breadth first traversal by @danielmorell in [#461](https://github.com/rollbar/pyrollbar/pull/461)

**1.1.0-alpha**

- Fixed shortener multi level shortening by @danielmorell and @pawelsz-rb. See [#449](https://github.com/rollbar/pyrollbar/pull/449)

**1.0.0**

- Fixed handling `sensitive_post_parameters` decorator in Django by @pawelsz-rb. See [#413](https://github.com/rollbar/pyrollbar/pull/413)
- Fixed Werkzeug DeprecationWarning of `BaseRequest`  by @compyman. See [#410](https://github.com/rollbar/pyrollbar/pull/410)
- Fixed missing locals shortening on items with "trace_chain" instead of "trace" by @terencehonles. See [#365](https://github.com/rollbar/pyrollbar/pull/365)
- Fixed FastAPI version comparison by @ayharano. See [#433](https://github.com/rollbar/pyrollbar/pull/433)
- Fixed #436 `WSGIRequest` has no attribute `sensitive_post_parameters`. by @danielmorell. See [#437](https://github.com/rollbar/pyrollbar/pull/437)
- Added new `thread_pool` handler by @danielmorell. See [#416](https://github.com/rollbar/pyrollbar/pull/416)
- Added Rollbar branding to the readme by @paulserraino. See [#418](https://github.com/rollbar/pyrollbar/pull/418)
- Added batched transform to increase sanitization and serialization performance by @ijsnow. See [#421](https://github.com/rollbar/pyrollbar/pull/421)
- Replaced unittest2 with unittest by @brianr. See [#420](https://github.com/rollbar/pyrollbar/pull/420)
- Removed unittest2 by @mcepl. See [#419](https://github.com/rollbar/pyrollbar/pull/419)
- Remove deprecated flask `before_first_request` by @albertyw. See [#428](https://github.com/rollbar/pyrollbar/pull/428)
- Removed support for Python 2 by @danielmorell. See [#435](https://github.com/rollbar/pyrollbar/pull/435)
- Updated the base Ubuntu for CI to 20.04 test runner by @danielmorell and @waltjones. See [#427](https://github.com/rollbar/pyrollbar/pull/427)
- Replaced `httpx.post` `data` kwarg with `content` by @ayharano. See [#425](https://github.com/rollbar/pyrollbar/pull/425)

**0.16.3**

- Pinned Python 2 CI tests to legacy version of dependencies. See [#408](https://github.com/rollbar/pyrollbar/pull/408)
- Add PyPI badge for supported Python versions. See [#408](https://github.com/rollbar/pyrollbar/pull/401)
- Add Django 4.0+ compatibility. See [#408](https://github.com/rollbar/pyrollbar/pull/400)
- Update PR template. See [#408](https://github.com/rollbar/pyrollbar/pull/395)
- SC-95272: Remove support for Python 3.3. See [#408](https://github.com/rollbar/pyrollbar/pull/394)

**0.16.2**

- Fix building person data in Django. See [#385](https://github.com/rollbar/pyrollbar/pull/385)
- Fix circular error logging for non-HTTP events in Starlette. See [#390](https://github.com/rollbar/pyrollbar/pull/390)
- Fix Python 3.4 builds. See [#389](https://github.com/rollbar/pyrollbar/pull/389)

**0.16.1**

- Fix PyPI artifacts

**0.16.0**

- Add support for FastAPI framework. See [#373](https://github.com/rollbar/pyrollbar/pull/373)
- Add support for Starlette framework. See [#373](https://github.com/rollbar/pyrollbar/pull/373)
- Add support for ASGI-based frameworks. See [#373](https://github.com/rollbar/pyrollbar/pull/373)
- Add support for HTTPX async handler. See [#373](https://github.com/rollbar/pyrollbar/pull/373)
- Add support for async report_exc_info and report_message. See [#373](https://github.com/rollbar/pyrollbar/pull/373)
- Collect user IP from X-Forwarded-For, fall back to X-Real-Ip. See [#370](https://github.com/rollbar/pyrollbar/pull/370)
- Improve examples. See [#368](https://github.com/rollbar/pyrollbar/pull/368)
- Fix Python 3.3 builds. See [#374](https://github.com/rollbar/pyrollbar/pull/374)
- Fix Flask 0.x builds. See [#376](https://github.com/rollbar/pyrollbar/pull/376)

**0.15.2**

- Add support for whitelist/blacklist for safelist/blocklist. See [#354](https://github.com/rollbar/pyrollbar/pull/343)
- Add Twisted to the available frameworks. See [#360](https://github.com/rollbar/pyrollbar/pull/360)

**0.15.1**

- Add support to Python 3.8. See [#351](https://github.com/rollbar/pyrollbar/pull/351)
- Fix deque test. See [#349](https://github.com/rollbar/pyrollbar/pull/349)
- Add alternatives to exception handler. See [#335](https://github.com/rollbar/pyrollbar/pull/335)
- Change dict_merge to allow strict mode. See [#339](https://github.com/rollbar/pyrollbar/pull/339)
- Improve scrubbing test case. See [#343](https://github.com/rollbar/pyrollbar/pull/343)

**0.15.0**

- Prevent recursive re-raising of exceptions. See [#317](https://github.com/rollbar/pyrollbar/pull/317)
- Correctly apply logger formatting to Rollbar messages. See [#312](https://github.com/rollbar/pyrollbar/pull/312)
- Fix deprecation warnings. See [#325](https://github.com/rollbar/pyrollbar/pull/319) and [#331](https://github.com/rollbar/pyrollbar/pull/331)
- Allow the request pool to be configured. See [#305](https://github.com/rollbar/pyrollbar/pull/305)
- Use callable() instead of try/except TypeError. See [#319](https://github.com/rollbar/pyrollbar/pull/319)
- Update Travis CI matrix. See [#317](https://github.com/rollbar/pyrollbar/pull/317)
- Fix Travis build errors. See [#328](https://github.com/rollbar/pyrollbar/pull/328)
- Update trove classifiers. See [#331](https://github.com/rollbar/pyrollbar/pull/331)

**0.14.7**

- Allow the raw request body to be included if desired. See [#304](https://github.com/rollbar/pyrollbar/pull/304)
- Send Rollbar access token in HTTP header. See [#303](https://github.com/rollbar/pyrollbar/pull/303)
- Add support for Django 1.7 & 1.8 in \_build_django_request_data. See [#301](https://github.com/rollbar/pyrollbar/pull/301)
- Add support for Quart framework. See [#300](https://github.com/rollbar/pyrollbar/pull/300)

**0.14.6**

- Add the authorization header to the default scrub fields list. See [#299](https://github.com/rollbar/pyrollbar/pull/299)
- Encode the payload properly for newer versions of Twisted. See [#298](https://github.com/rollbar/pyrollbar/pull/298)
- Don't fail to send payloads because some inner object is not JSON serializable. See [#297](https://github.com/rollbar/pyrollbar/pull/297)
- Allow floats as circular references. See [#291](https://github.com/rollbar/pyrollbar/pull/291)

**0.14.5**

- Fix bug in which error params were not being passed correctly to Pyramid middleware. See [#287](https://github.com/rollbar/pyrollbar/pull/287)

**0.14.4**

- Fix bug in Pyramid middleware where exc_info was not being passed to handle_error. See [#283](https://github.com/rollbar/pyrollbar/pull/283)
- Fix bug where errors in the serialization of local variables caused errors to be dropped. They will now make it to Rollbar. See [#284](https://github.com/rollbar/pyrollbar/pull/284)

**0.14.3**

- Add support for HTTP(S) proxies. See [#276](https://github.com/rollbar/pyrollbar/pull/276)

**0.14.2**

- Fix bug with file-based logging config in Python 3. See [#277](https://github.com/rollbar/pyrollbar/issues/277)
- Fix bug in Django middleware when request has no META attribute. See [#273](https://github.com/rollbar/pyrollbar/pull/273)

**0.14.1**

- Add Django middlewares that differentiate between 404 and other exceptions. See [#270](https://github.com/rollbar/pyrollbar/pull/270)
- Make Werkzeug request handling more general. See [#271](https://github.com/rollbar/pyrollbar/pull/271)
- Fix incorrect handling rollbar.init() arguments when using LOGGER in Django. See [#235](https://github.com/rollbar/pyrollbar/pull/235)
- Use thread local storage for not thead-safe requests.Sessions. See [#269](https://github.com/rollbar/pyrollbar/pull/269)
- Swallow known error that happens in add_person_data. See [#268](https://github.com/rollbar/pyrollbar/pull/268)
- Only write a log about a rate limit once. See [#267](https://github.com/rollbar/pyrollbar/pull/267)
- Adapt Django view monkey patch to support Django 2. See [#257](https://github.com/rollbar/pyrollbar/pull/257)
- Add support request objects from Django REST framework. See [#18](https://github.com/rollbar/pyrollbar/pull/18)
- Add support for Falcon framework requests. See [#51](https://github.com/rollbar/pyrollbar/pull/51)
- Add support for Django Channels' AsgiRequest. See [#272](https://github.com/rollbar/pyrollbar/pull/272)

**0.14.0**

- Create the configuration options, `capture_username` and `capture_email`. Prior to this release,
  if we gather person data automatically, we would try to capture the id, email, and username.
  Starting with this release by default we will only capture the id. If you set `capture_username`
  to `True` then we will also attempt to capture the username. Similarly for `capture_email` with
  the email. (See [#262](https://github.com/rollbar/pyrollbar/pull/262))
- Create the configuration option `capture_ip`. This can take one of three values: `True`,
  `'anonymize'`, or `False`. This controls how we handle IP addresses that are captured from
  requests. If `True`, then we will send the full IP address. This is the current behaviour and the
  default. If set to the string `'anonymize'` which is also available as the constant `ANONYMIZE` on
  the `rollbar` module, we will mask out the least significant bits of the IP address. If set to
  `False`, then we will not capture the IP address. (See [#262](https://github.com/rollbar/pyrollbar/pull/262))
- Fix `request.files_keys` for Flask [#263](https://github.com/rollbar/pyrollbar/pull/263)
- If you call `init` multiple times we will update the settings at each call. Prior to
  this release we emitted a warning and did not update settings. [#259](https://github.com/rollbar/pyrollbar/pull/259)
- Better Tornado support [#256](https://github.com/rollbar/pyrollbar/pull/256)

**0.13.18**

- See Release Notes

**0.13.17**

- Fix deprecation warning related to Logging.warn
- Fix bug where non-copyable objects could cause an exception if they end up trying to get passed to
  one of the logging methods.
- Fix bug where both `trace` and `trace_chain` could appear in the final payload, which is not
  allowed by the API.

**0.13.16**

- Fix PyPI documentation

**0.13.15**

- Fix shortener issue for Python 3

**0.13.14**

- Fix bug that caused some payload objects to be turned into the wrong type when
shortening is applied. This would lead to API rejections. See [#200](https://github.com/rollbar/pyrollbar/pull/200)
- Add `suppress_reinit_warning` option if you want to allow calling init twice. See [#198](https://github.com/rollbar/pyrollbar/pull/198)
- Pass through keyword arguments from the logging handler to the underling Rollbar init call. See
  [#203](https://github.com/rollbar/pyrollbar/pull/203)

**0.13.13**

- Add support for AWS Lambda. See [#191](https://github.com/rollbar/pyrollbar/pull/191)

**0.13.12**

- Remove the Django request body from the payload as it can contain sensitive data. See [#174](https://github.com/rollbar/pyrollbar/pull/174)
- Allow users to shorten arbitrary parts of the payload. See [#173](https://github.com/rollbar/pyrollbar/pull/173)
- Fix a Django deprecation warning. See [#165](https://github.com/rollbar/pyrollbar/pull/165)

**0.13.11**

- Handle environments where `sys.argv` does not exist. See [#131](https://github.com/rollbar/pyrollbar/pull/131)

**0.13.10**

- Gather request method from WebOb requests. See [#152](https://github.com/rollbar/pyrollbar/pull/152)

**0.13.9**

- Change `_check_config()` to deal with agent handler. See [#147](https://github.com/rollbar/pyrollbar/pull/147)
- Fix settings values not being booleans in Pyramid. See [#150](https://github.com/rollbar/pyrollbar/pull/150)

**0.13.8**

- Fix regression from 0.13.7. See [#141](https://github.com/rollbar/pyrollbar/pull/141)

**0.13.7**

- Update Django middleware to support Django 1.10+. See [#138](https://github.com/rollbar/pyrollbar/pull/138)

**0.13.6**

- Fixed a referenced before assignment in the failsafe. See [#136](https://github.com/rollbar/pyrollbar/pull/136)

**0.13.5**

- Fixed record message formatting issues breaking the log handler's history. See [#135](https://github.com/rollbar/pyrollbar/pull/135)

**0.13.4**

- Fixed failsafe handling for payloads that are too large. See [#133](https://github.com/rollbar/pyrollbar/pull/133)

**0.13.3**

- Improved handling of Enums. See [#121](https://github.com/rollbar/pyrollbar/pull/121)

**0.13.2**

- Improved handling of Nan and (Negative)Infinity. See [#117](https://github.com/rollbar/pyrollbar/pull/117)
- RollbarHandler now ignores log records from Rollbar. See [#118](https://github.com/rollbar/pyrollbar/pull/118)

**0.13.1**

- Failsafe handling for payloads that are too large. See [#116](https://github.com/rollbar/pyrollbar/pull/116)
  - Failsafe Behavior
    - Log an error containing the original payload and the UUID from it
    - Send a new payload to Rollbar with the custom attribute containing the UUID and host from the original payload

**0.13.0**

- Frame payload refactor and varargs scrubbing. See [#113](https://github.com/rollbar/pyrollbar/pull/113)
  - Frame Payload Changes
    - remove args and kwargs
    - add argspec as the list of argument names to the function call
    - add varargspec as the name of the list containing the arbitrary unnamed positional arguments to the function call if any exist
    - add keywordspec as the name of the object containing the arbitrary keyword arguments to the function call if any exist
  - Other Changes:
    - Arguments with default values are no longer removed from args and placed into kwargs
    - varargs are now scrubbable and scrubbed by default
- Switched to using a Session object to perform HTTPS requests to optimize for keepalive connections. See [#114](https://github.com/rollbar/pyrollbar/pull/114)

**0.12.1**

- Keep blank values from request query strings when scrubbing URLs. See [#110](https://github.com/rollbar/pyrollbar/pull/110)

**0.12.0**

- Fix and update Twisted support. See [#109](https://github.com/rollbar/pyrollbar/pull/109)
  - **Breaking Changes**: [treq](https://github.com/twisted/treq) is now required for using Twisted with pyrollbar.

**0.11.6**

- Improve object handling for SQLAlchemy. See [#108](https://github.com/rollbar/pyrollbar/pull/108)

**0.11.5**

- Fixed a bug when custom `__repr__()` calls resulted in an exception being thrown. See [#102](https://github.com/rollbar/pyrollbar/pull/102)

**0.11.4**

- Revert changes from 0.11.3 since they ended-up having the unintended side effect by that exceptions messages weren't processing as expected.
- Update settings in init first so that custom scrub_fields entries are handled correctly

**0.11.3**

- Obey safe repr for exceptions.  See [#91](https://github.com/rollbar/pyrollbar/pull/91)

**0.11.2**
- Fixed a bug when calling logging.exception() when not in an exception handler.  Now it correctly determines it doesn't have any exception info and uses report_message() instead of report_exc_info().

**0.11.1**
- Added a new configuration option to expose the serializer's `safelisted_types` param
  - Allows users to safelist types to be serialized using `repr(obj)` instead of `str(type(obj))`
- Fixed a bug that was not taking the `safe_repr` option into account. See [#87](https://github.com/rollbar/pyrollbar/pull/87)

**0.11.0**
- Overhauled the scrubbing and serialization mechanisms to provide deep object scrubbing and better handling of UTF-8 data from local variables. See [#75](https://github.com/rollbar/pyrollbar/pull/75)
  - This fixes a bunch of problems with reporting local variables, including `UnicodeEncodeError`s and attempting to read variables after the thread they were in has died.
- Local variables and payload data is now sent over in their original structure.
  - If a variable was a `dict`, it will be transmitted as a `dict` instead of turned into a string representation of the variable.
- The entire payload is now scrubbed and URL password fields are scrubbed as well.
- Added a Django example.
- Wrote many, many more tests :)
- Integrated the `six` library to provide cleaner support for Python3.
- Added some additional scrub fields.

**0.10.1**
- Added a warning message if `init()` is called more than once.

**0.10.0**
- Added support for Twisted framework. See [#69](https://github.com/rollbar/pyrollbar/pull/69)
- Fix a bug that was causing max recursion errors while collecting local variables. See [#77](https://github.com/rollbar/pyrollbar/pull/77)
  - Added a configuration option, `safe_repr: True` which will cause payload serialization to use the type name for non-built-in objects.
    This option defaults to `True` which may cause data reported to Rollbar to contain less information for custom types.
    Prior to this change, serialization of custom objects called `__repr__()` which may have had undesired side effects.
- Fixed a bug that did not correctly handle anonymous tuple arguments while gathering local variables.

**0.9.14**
- Fix logging loop when using Flask in a non-request context, and also using the Rollbar logging handler. See [#68](https://github.com/rollbar/pyrollbar/pull/68)

**0.9.13**
- If present, get request from log record. Otherwise try to guess current request as usual.

**0.9.12**
- Fix a bug that was causing a crash while reporting an error that happened in a Werkzeug request that had no `request.json`. See [#64](https://github.com/rollbar/pyrollbar/pull/64)

**0.9.11**
- Implement workarounds for NaN and Infinity "numbers" in payloads. See [#62](https://github.com/rollbar/pyrollbar/pull/62)

**0.9.10**
- Fix request data collection in Flask 0.9. See [#61](https://github.com/rollbar/pyrollbar/pull/61)

**0.9.9**
- Add exception handler for RQ (requires some instrumentation). See [#57](https://github.com/rollbar/pyrollbar/pull/57)
- Scrub fields inside `extra_data`
- Gather the process PID and report it along with the other 'server' data

**0.9.8**
- Support bare WSGI requests ([#55](https://github.com/rollbar/pyrollbar/pull/55))

**0.9.7**
- Add support for Google App Engine ([#53](https://github.com/rollbar/pyrollbar/pull/53))

**0.9.6**
- Fix memory leak when using the RollbarHandler logging handler (see [#43](https://github.com/rollbar/pyrollbar/pull/43))
- Fix bug where named function arguments were not scrubbed correctly

**0.9.5**
- Fix bug with local variable gathering that was breaking when getting the arguments for a class constructor.

**0.9.4**
- Request headers are now scrubbed, [pr#41](https://github.com/rollbar/pyrollbar/pull/41).

**0.9.3**
- `exception_level_filters` can now take a string that defines the class to filter, [#38](https://github.com/rollbar/pyrollbar/pull/38).

**0.9.2**
- Added an option to disable SSL certificate verification, [#36](https://github.com/rollbar/pyrollbar/pull/36).
- Added `__version__` specifier to `__init__.py`.

**0.9.1**

New features:

- For Tornado requests, gather the request start time. See [#33](https://github.com/rollbar/pyrollbar/pull/33)
- Add handler which uses Tornado's `AsyncHTTPClient`. To use this, set your 'handler' to 'tornado'. See [#34](https://github.com/rollbar/pyrollbar/pull/34)


**0.9.0**

- Improvements to RollbarHandler logging handler. It now:
  - extracts more information out of each record (i.e. metadata like pathname and creation time)
  - uses the format string, with arguments not yet replaced, as the main message body. This will result in much better grouping in Rollbar.

Note about upgrading from 0.8.x: unless you are using RollbarHandler, there are no breaking changes. If you are using RolbarHandler, then this will change the way your data appears in Rollbar (to the better, in our opinion).

**0.8.3**
- Provide a way to blocklist types from being repr()'d while gathering local variables.

**0.8.2**
- Fix uncaught ImproperlyConfigured exception when importing Rollbar in a Django REST Framework environment without a settings module loaded ([#28](https://github.com/rollbar/pyrollbar/pull/28))

**0.8.1**
- Only attempt local variable extraction if traceback frames are of the correct type, print a warning otherwise
- Fix JSON request param extraction for Werkzeug requests (Pyramid, Flask, etc)

**0.8.0**
- Local variables collection now enabled by default.
- Fixed scrubbing for utf8 param names.

**0.7.6**
- Added local variables for all in-project frames and the last frame.

**0.7.5**
- Initial support for sending args and kwargs for traceback frames.
- Optimization to send the access token in a header.

**0.7.4**
- Level kwarg added to `rollbar.report_exc_info()` ([#22](https://github.com/rollbar/pyrollbar/pull/22))

**0.7.3**
- Added in an optional `endpoint` parameter to `search_items()`.

**0.7.2**
- Fix for scrubbing werkzeug json bodies ([#20](https://github.com/rollbar/pyrollbar/pull/20))

**0.7.1**
- Support scrubbing for werkzeug json bodies ([#19](https://github.com/rollbar/pyrollbar/pull/19))

**0.7.0**
- Python 3 support
- Now support extracting data from Django REST framework requests
- New `enabled` configuration setting

**0.6.2**
- Fixed json request data formatting for reports in Bottle requests
- Now send json request data for Django and Pyramid apps
- Set framework and request context properly for all reports in Flask and Bottle apps

**0.6.1**
- Added Django, Pyramid, Flask and Bottle support for default contexts.

**0.6.0**
- `report_message()` now returns the UUID of the reported occurrence.

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
