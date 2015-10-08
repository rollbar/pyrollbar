import re

from rollbar.lib import iteritems, map, urlsplit, urlencode, urlunsplit, parse_qs
from rollbar.lib.transforms.scrub import ScrubTransform


_starts_with_auth_re = re.compile(r'^[a-zA-Z0-9-_]*(:[^@/]+)?@')
_starts_with_colon_double_slash = re.compile(r'^:?//')

class ScrubUrlTransform(ScrubTransform):
    def __init__(self,
                 suffixes=None,
                 scrub_username=False,
                 scrub_password=True,
                 params_to_scrub=None,
                 redact_char='-',
                 randomize_len=True):

        super(ScrubUrlTransform, self).__init__(suffixes=suffixes,
                                                redact_char=redact_char,
                                                randomize_len=randomize_len)
        self.scrub_username = scrub_username
        self.scrub_password = scrub_password
        self.params_to_scrub = set(map(lambda x: x.lower(), params_to_scrub))

    def _in_scrub_fields(self, key):
        if not key:
            # This can happen if the transform is applied to a non-object,
            # like a string.
            return True
        return super(ScrubUrlTransform, self)._in_scrub_fields(key)

    def _scrub_url(self, url_string, key=None):
        missing_scheme = False
        missing_colon_double_slash = False

        if _starts_with_colon_double_slash.match(url_string):
            missing_scheme = True
            url_string = 'remove:%s' % url_string.lstrip(':')
        elif _starts_with_auth_re.match(url_string):
            missing_scheme = True
            missing_colon_double_slash = True
            url_string = 'remove://%s' % url_string

        try:
            url_parts = urlsplit(url_string)
            qs_params = parse_qs(url_parts.query)
        except:
            return url_string

        netloc = url_parts.netloc

        # If there's no netloc, give up
        if not netloc:
            return url_string

        for qs_param, vals in iteritems(qs_params):
            if qs_param.lower() in self.params_to_scrub:
                vals2 = map(self._redact, vals)
                qs_params[qs_param] = vals2

        scrubbed_qs = urlencode(qs_params, doseq=True)

        if self.scrub_username and url_parts.username:
            redacted_username = self._redact(url_parts.username)
            netloc = netloc.replace(url_parts.username, redacted_username)

        if self.scrub_password and url_parts.password:
            redacted_pw = self._redact(url_parts.password)
            netloc = netloc.replace(url_parts.password, redacted_pw)

        scrubbed_url = (url_parts.scheme if not missing_scheme else '',
                        netloc,
                        url_parts.path,
                        scrubbed_qs,
                        url_parts.fragment)

        scrubbed_url_string = urlunsplit(scrubbed_url)

        if missing_colon_double_slash:
            scrubbed_url_string = scrubbed_url_string.lstrip('://')

        return scrubbed_url_string

    def default(self, o, key=None):
        # Reset the default behavior back to a no-op since we are
        # only interested in scrubbing strings that represent URLs
        return o

    def transform_py2_str(self, o, key=None):
        if self._in_scrub_fields(key):
            return self._scrub_url(o, key=key)
        return super(ScrubUrlTransform, self).transform_py2_str(o, key=key)

    def transform_py3_bytes(self, o, key=None):
        if self._in_scrub_fields(key):
            return self._scrub_url(o, key=key)
        return super(ScrubUrlTransform, self).transform_py3_bytes(o, key=key)

    def transform_unicode(self, o, key=None):
        if self._in_scrub_fields(key):
            return self._scrub_url(o, key=key)
        return super(ScrubUrlTransform, self).transform_unicode(o, key=key)


__all__ = ['ScrubUrlTransform']
