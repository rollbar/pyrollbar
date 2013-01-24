# Change Log

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

