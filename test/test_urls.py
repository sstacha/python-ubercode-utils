import unittest
from contextlib import redirect_stdout
from io import StringIO

from ubercode.utils.urls import ParsedUrl
from ubercode.utils.urls import ParsedQueryString


class TestUrls(unittest.TestCase):

    # -------- ParsedUrl class ----------

    # --- constructor defaults
    # ------------------------
    def test_constructor(self):
        # test rel with default path
        rel_uri = "1.jpg"
        parsed_url = ParsedUrl(rel_uri, default_netloc='ex.org', default_scheme='http', default_filepath='/mdb')
        self.assertEqual("http://ex.org/mdb/1.jpg", str(parsed_url))
        # test rel url with just querystring and a default filepath
        rel_uri = "?id=1&b=2"
        parsed_url = ParsedUrl(rel_uri, default_netloc='ex.org', default_scheme='http', default_filepath='/mdb')
        self.assertEqual("http://ex.org/mdb/?id=1&b=2", str(parsed_url))
        # test rel url with no defaults gives back the rel url
        test_uri = "/?id=1&b=2"
        parsed_url = ParsedUrl(test_uri)
        self.assertEqual(test_uri, str(parsed_url))
        # test rel with netloc gives scheme independent result
        parsed_url = ParsedUrl(test_uri, default_netloc='ex.org')
        self.assertEqual("//ex.org/?id=1&b=2", str(parsed_url))
        # test rel with netloc and scheme gives fully qualified url
        parsed_url = ParsedUrl(test_uri, default_netloc='ex.org', default_scheme='https')
        self.assertEqual("https://ex.org/?id=1&b=2", str(parsed_url))
        # test rel with scheme but no netloc gives rel back
        parsed_url = ParsedUrl(test_uri, default_scheme='https')
        self.assertEqual(test_uri, str(parsed_url))
        # test domain uri with default_scheme returns fully qualified url
        test_uri = "//ex.org/?id=1&b=2"
        parsed_url = ParsedUrl(test_uri)
        self.assertEqual(test_uri, str(parsed_url))
        parsed_url = ParsedUrl(test_uri, default_scheme='https')
        self.assertEqual("https:" + test_uri, str(parsed_url))
        # test that mailto and tel links don't get defaulted
        test_uri = 'mailto:me@mail.com?subject=mysubject&body=mybody'
        parsed_url = ParsedUrl(test_uri, default_scheme='http', default_netloc='localhost:8000', default_filepath='/booger/')
        self.assertEqual("mailto", str(parsed_url.scheme))
        self.assertEqual(test_uri, parsed_url.url)
        test_uri = 'tel: 222.222.2222'
        parsed_url = ParsedUrl(test_uri, default_scheme='http', default_netloc='localhost:8000', default_filepath='/booger/')
        self.assertEqual("tel", str(parsed_url.scheme))
        self.assertEqual(test_uri, parsed_url.url)


    # --- basic retrieval
    # -------------------
    # NOTE: not testing the base parsed value from urllib only differences
    def test_retrieval(self):
        # hostname is domain instead; but can be gotten from raw property and are equal
        test_uri = "/?id=1&b=2"
        parsed_url = ParsedUrl(test_uri)
        self.assertEqual("", parsed_url.scheme)
        self.assertEqual(None, parsed_url.domain)
        self.assertEqual("", parsed_url.netloc)
        self.assertEqual(parsed_url.parsed.hostname, parsed_url.domain)
        with self.assertRaises(AttributeError):
            parsed_url.hostname
        # root domain is none if we don't have a domain
        self.assertEqual(None, parsed_url.root_domain)
        # constructor needs the //ex.org but we can set the domain without it
        parsed_url.domain = "ex.org"
        self.assertEqual(f"//ex.org{test_uri}", str(parsed_url))
        # root domain is ex.org if set
        self.assertEqual(parsed_url.domain, parsed_url.root_domain)
        # unlike hostname we allow setting the domain for changing url links ex: //dev.ex.org/... -> //qa.ex.org/...
        # test that the setting of the domain that previously had a port keeps the port
        test_uri = "//localhost:8000/test/index.html?x=1&y=2#test"
        parsed_url = ParsedUrl(test_uri)
        parsed_url.domain = "test.local.net"
        self.assertEqual("//test.local.net:8000/test/index.html?x=1&y=2#test", str(parsed_url))
        self.assertEqual("test.local.net", parsed_url.domain)
        self.assertEqual("test.local.net:8000", parsed_url.netloc)
        # created convenience methods for common items like filename filepath and file extension from path
        self.assertEqual(".html", parsed_url.fileext)
        self.assertEqual("index.html", parsed_url.filename)
        self.assertEqual("/test", parsed_url.filepath)
        self.assertEqual("/test/index.html", parsed_url.path)
        # base url is the url without any querystring or fragments
        self.assertEqual("//test.local.net:8000/test/index.html", parsed_url.base)
        # (site) relative url is url with querystring and fragments but no scheme or netloc
        # NOTE: very handy for taking fully qualified urls to relative ones for different environments
        # Ex: https://dev.ex.org/test/index.html?x=1#test -> /test/index.html?x=1#test
        self.assertEqual("/test/index.html?x=1&y=2#test", parsed_url.rel)
        # allow fully replacing the querystring and fragment which isn't allowed in urllib
        parsed_url.qs = "z=1&u=3"
        self.assertEqual("//test.local.net:8000/test/index.html?z=1&u=3#test", str(parsed_url))
        parsed_url.fragment = "test2"
        self.assertEqual("//test.local.net:8000/test/index.html?z=1&u=3#test2", str(parsed_url))
        # it is very handy to change just one parameter instead of the whole qs
        # test setParam will add if not there
        parsed_url.set_param("v", 4)
        self.assertEqual("//test.local.net:8000/test/index.html?z=1&u=3&v=4#test2", str(parsed_url))
        # test updates if there
        parsed_url.set_param("u", "2")
        self.assertEqual("//test.local.net:8000/test/index.html?z=1&u=2&v=4#test2", str(parsed_url))
        # test removing a param
        parsed_url.del_param("u")
        self.assertEqual("//test.local.net:8000/test/index.html?z=1&v=4#test2", str(parsed_url))

        # bugfix #1: test that we don't truncate data if there is an = in the data
        test_qs = "id=1&b=2&x=1234=56&z=3"
        parsed_qs = ParsedQueryString(test_qs)
        self.assertEqual(test_qs, str(parsed_qs))

        # bugfix #2: test that we get the correct values when we use a site relative path like /products/ and a
        #   default_filepath like /blog/; also check for passing or not passing ending slash
        test_uri = "/products/"
        parsed_url = ParsedUrl(test_uri, default_scheme="http", default_netloc="localhost:8000",
                               default_filepath="/blog")
        self.assertEqual(parsed_url.url, "http://localhost:8000/products/")
        test_uri = "./products/"
        parsed_url = ParsedUrl(test_uri, default_scheme="http", default_netloc="localhost:8000",
                               default_filepath="/blog")
        self.assertEqual(parsed_url.url, "http://localhost:8000/blog/products/")
        test_uri = "../products/"
        parsed_url = ParsedUrl(test_uri, default_scheme="http", default_netloc="localhost:8000",
                               default_filepath="/blog")
        self.assertEqual(parsed_url.url, "http://localhost:8000/products/")
        test_uri = "."
        parsed_url = ParsedUrl(test_uri, default_scheme="http", default_netloc="localhost:8000",
                               default_filepath="/blog")
        self.assertEqual(parsed_url.url, "http://localhost:8000/blog/")
        test_uri = "."
        parsed_url = ParsedUrl(test_uri, default_scheme="http", default_netloc="localhost:8000",
                               default_filepath="/blog/")
        self.assertEqual(parsed_url.url, "http://localhost:8000/blog/")


if __name__ == '__main__':
    unittest.main()

