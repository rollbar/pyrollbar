import collections
import copy

from rollbar.lib import iteritems, transforms, string_types, urlparse, parse_qs
from rollbar.lib.transforms.scruburl import ScrubUrlTransform

from rollbar.test import BaseTest, SNOWMAN


class ScrubUrlTransformTest(BaseTest):
    def _assertScrubbed(self,
                        params_to_scrub,
                        start,
                        expected,
                        scrub_username=False,
                        scrub_password=True,
                        redact_char='-',
                        skip_id_check=False):
        scrubber = ScrubUrlTransform(params_to_scrub=params_to_scrub,
                                     scrub_username=scrub_username,
                                     scrub_password=scrub_password,
                                     redact_char=redact_char,
                                     randomize_len=False)
        result = transforms.transform(start, scrubber)

        print start
        print result
        print expected

        if not skip_id_check:
            self.assertNotEqual(id(result), id(expected))

        self.assertEqual(type(result), type(expected))
        self.assertIsInstance(result, string_types)
        self._compare_urls(expected, result)

    def _compare_urls(self, url1, url2):
        parsed_urls = map(urlparse, (url1, url2))
        qs_params = map(lambda x: parse_qs(x.query), parsed_urls)
        num_params = map(len, qs_params)
        param_names = map(lambda x: set(x.keys()), qs_params)

        self.assertEqual(*num_params)
        self.assertDictEqual(*qs_params)
        self.assertSetEqual(*param_names)

        for facet in ('scheme', 'netloc', 'path', 'params', 'username', 'password', 'hostname', 'port'):
            comp = map(lambda x: getattr(x, facet), parsed_urls)
            self.assertEqual(*comp)

    def test_no_scrub(self):
        obj = 'http://hello.com/?foo=bar'
        expected = obj
        self._assertScrubbed(['password'], obj, expected)

    def test_not_url(self):
        obj = 'I am a plain\'ol string'
        expected = obj
        self._assertScrubbed(['password'], obj, expected, skip_id_check=True)

    def test_scrub_simple_url_params(self):
        obj = 'http://foo.com/asdf?password=secret'
        expected = obj.replace('secret', '------')
        self._assertScrubbed(['password'], obj, expected)

    def test_scrub_multi_url_params(self):
        obj = 'http://foo.com/asdf?password=secret&password=secret2&token=TOK&clear=text'
        expected = obj.replace('secret2', '-------').replace('secret', '------').replace('TOK', '---')
        self._assertScrubbed(['password', 'token'], obj, expected)

    def test_scrub_password_auth(self):
        obj = 'http://cory:secr3t@foo.com/asdf?password=secret&clear=text'
        expected = obj.replace('secr3t', '------').replace('secret', '------')
        self._assertScrubbed(['password'], obj, expected)

    def test_scrub_username_auth(self):
        obj = 'http://cory:secr3t@foo.com/asdf?password=secret&clear=text'
        expected = obj.replace('cory', '----').replace('secret', '------')
        self._assertScrubbed(['password'], obj, expected, scrub_password=False, scrub_username=True)

    def test_scrub_username_and_password_auth(self):
        obj = 'http://cory:secr3t@foo.com/asdf?password=secret&clear=text'
        expected = obj.replace('cory', '----').replace('secr3t', '------').replace('secret', '------')
        self._assertScrubbed(['password'], obj, expected, scrub_password=True, scrub_username=True)

    def test_scrub_missing_scheme(self):
        obj = '//cory:secr3t@foo.com/asdf?password=secret&clear=text'
        expected = obj.replace('secr3t', '------').replace('secret', '------')
        self._assertScrubbed(['password'], obj, expected)

    def test_scrub_missing_scheme_and_double_slash(self):
        obj = 'cory:secr3t@foo.com/asdf?password=secret&clear=text'
        expected = obj.replace('secr3t', '------').replace('secret', '------')
        self._assertScrubbed(['password'], obj, expected)
