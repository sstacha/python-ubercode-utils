import os
from urllib.parse import urlsplit
from ubercode.utils.convert import to_str, to_int
from pathlib import PurePath
from .convert import to_mask

class ParsedQueryString:
    """
    Encapsulates the parsing and setting of query string parameters
    """
    def __init__(self, query_string):
        self.original_qs = query_string
        self.qs = query_string.strip()
        # strip off the ? if still there
        if self.qs.startswith("?"):
            self.qs = self.qs[1:]
        # split each param based on & (should be x=xval, y=yval etc)
        exp_params = self.qs.split("&")
        self.params = {}
        for exp_param in exp_params:
            param = to_str(exp_param)
            key = ""
            value = ""
            pos = param.find("=")
            if pos > -1:
                key = param[:pos]
                if len(param) > pos + 1:
                    value = param[pos + 1:]
            else:
                if param:
                    key = param
            if key:
                self.params[key] = value

    def __str__(self):
        """
        By default, the query string will be the params dict put back together without the ?
        :return:
        """
        qs = ""
        for key, value in self.params.items():
            qs += key + "=" + str(value) + "&"
        if qs:
            qs = qs[:-1]
        return qs


class ParsedUrl:
    """
        Encapsulates the parsing and setting up url values so we don't have this code everywhere being done differently.
        Basic idea is to pass a string url (possibly relative) and a default_scheme and netloc to create absolute urls.
        Then allow developers to get or adjust the values they need.

        Ex: {url=test.html, default_netloc=//www.ex.org} -> //www.ex.org/test.html
        Ex: {url=https://www.site2.com/something/, default_netloc=//www.ex.org} -> https://site2.com/something/
        Ex: {url=test.html, default_netloc=None} -> test.html

        We want a way to ask for a relative or fully qualified url including fragments and querystings or not
    """
    def __init__(self, url: str, default_netloc: str = None, default_scheme: str = None,
                 default_filepath: str = None, allow_fragments: bool = True, symlinks=False):
        self.original_url = url
        if self.url_filter(url) is None or len(self.url_filter(url)) == 0:
            raise Exception(
                f'Attempted to parse [{str(self.url_filter(url))}].  Url parameter must exist and be a relative or absolute url after filtering!')
        self.parsed = urlsplit(self.url_filter(url), default_scheme or "", allow_fragments=allow_fragments)
        if default_scheme and not self.parsed.scheme and self.netloc:
            self.scheme = default_scheme
        if default_netloc and not self.parsed.netloc and self.scheme in ["http", "https", ""]:
            self.netloc = default_netloc
        if default_filepath and default_filepath not in self.filepath and self.scheme in ["http", "https", ""]:
            # we have a parent path we need to append to the existing one
            new_path = str(PurePath(default_filepath, self.path))
            # note: I don't want .. since this is web urls; using normpath to remove them unless symlinks is true
            if not symlinks and '..' in new_path:
                new_path = os.path.normpath(new_path)
            # PurePath always strips the last path.  If we had a path before appending lets add it back
            if self.path.endswith('/') and not new_path.endswith('/'):
                new_path += '/'
            # if we only have the default path make sure we have a slash (since we know it is a path)
            #   note: PurePath will strip it off even if we send it
            if new_path.endswith(default_filepath) or new_path.endswith(default_filepath[:-1]) and not new_path.endswith('/'):
                new_path += '/'
            self.path = new_path
        # one last correction; if we have a scheme but no netloc lets omit the scheme so it doesn't give bad results
        if not self.parsed.netloc and self.parsed.scheme and self.parsed.scheme in ['http', 'https']:
            self.parsed = self.parsed._replace(scheme='')

    @property
    def filepath(self):
        return os.path.dirname(self.parsed.path)

    @property
    def filename(self):
        return os.path.basename(self.parsed.path)

    @property
    def fileext(self):
        return os.path.splitext(self.filename)[1]

    @property
    def url(self):
        # NOTE: since we are joining and applying filters in the constructor we just return the value here
        #   no setter needed to force constructor only
        return self.parsed.geturl()

    @property
    def base(self):
        # NOTE: url_base is always the current parsed minus any qs or fragment values
        return self.parsed._replace(query='', fragment='').geturl()

    @property
    def rel(self):
        # NOTE: url_rel is the current parsed minus any scheme or domain
        return self.parsed._replace(netloc='', scheme='').geturl()

    @property
    def port(self):
        # NOTE: port is set by netloc but readable separately
        return self.parsed.port

    @property
    def qs(self):
         return self.parsed.query

    @qs.setter
    def qs(self, value):
        self.parsed = self.parsed._replace(query=value)

    @property
    def fragment(self):
        return self.parsed.fragment

    @fragment.setter
    def fragment(self, value):
        self.parsed = self.parsed._replace(fragment=value)

    # adding the netloc back in since domain = hostname
    @property
    def netloc(self):
        return self.parsed.netloc

    @netloc.setter
    def netloc(self, value):
        self.parsed = self.parsed._replace(netloc=value)

    @property
    def domain(self):
        return self.parsed.hostname

    @domain.setter
    def domain(self, value):
        if self.parsed.port and str(self.parsed.port) not in value:
            value += f":{self.parsed.port}"
        self.parsed = self.parsed._replace(netloc=value)

    @property
    def scheme(self):
        return self.parsed.scheme

    @scheme.setter
    def scheme(self, value):
        self.parsed = self.parsed._replace(scheme=value)

    @property
    def path(self):
        return self.parsed.path

    @path.setter
    def path(self, value):
        self.parsed = self.parsed._replace(path=value)

    @property
    def root_domain(self):
        domain = self.domain
        if domain:
            pos = domain.rfind(".")
            if pos > -1:
                pos = domain.rfind(".", 0, pos)
                if pos > -1:
                    return domain[pos + 1:]
        return domain

    def get_param(self, key):
        pqs = ParsedQueryString(self.qs)
        return pqs.params.get(key, None)

    def set_param(self, key, value):
        # first load our existing params so we replace if it exists
        pqs = ParsedQueryString(self.qs)
        pqs.params[key] = value
        self.parsed = self.parsed._replace(query=str(pqs))

    def del_param(self, key):
        # first load our existing params so we replace if it exists
        pqs = ParsedQueryString(self.qs)
        if key in pqs.params:
            pqs.params.pop(key)
        self.parsed = self.parsed._replace(query=str(pqs))

    @staticmethod
    def url_filter(url):
        """
        Allows for modifying the url parameter before any parsing
        :return: modified url
        """
        # by default, we will simply strip any leading/trailing whitespace
        if url:
            return url.strip()
        return url

    def __str__(self):
        """
        By default, the string value is the fully qualified url (as much as we have)
        :return:
        """
        return self.url

class DjUrl:
    engine = None
    user = None
    password = None
    host = None
    port = None
    name = None

    def __init__(self, dj_url: str = None) -> None:
        """
        parses a packed "django_url" into its parts following similar rules to SqlAlchemy
        format: engine://user:password@host[:port]/dbname
        example: django.db.backends.mysql://scott:tiger@localhost:1366/test

        NOTE: asking for the string value will give back the original packed url masking the password
        NOTE: to_dict will give back the dictionary values to be added or replaced in the DATABASES dict

        :param url: packed django url  ex: django.db.backends.mysql://scott:tiger@localhost:1366/test
        """
        dj_url = dj_url or ""
        dj_url = dj_url.strip()
        encoded = False
        if dj_url.endswith('?--atencoded'):
            encoded = True
            dj_url = dj_url[:-len('?--atencoded')].strip()
        if not dj_url:
            return
        pos = dj_url.find('://')
        if pos > -1:
            self.engine = dj_url[:pos].strip() or None
            constr = dj_url[pos + len('://'):].strip()
        else:
            constr = dj_url
        pos = constr.find("@")
        if pos > -1:
            loginstr = constr[:pos].strip()
            constr = constr[pos + len("@"):].strip()
            pos = loginstr.find(':')
            if pos > -1:
                self.user = loginstr[:pos].strip() or None
                self.password = loginstr[pos + len(':'):].strip() or None
                if encoded:
                    self.password = self.password.replace('%40', '@')
            elif len(loginstr) > 0:
                self.user = loginstr or None
        else:
            # since password is the most common replacement look for that specifically next if we didn't have an @
            # NOTE: since password can contain / we will assume the only thing there is the password otherwise use @
            # Ex: DjUrl(':newpassword/newdatabase') -> password=newpassword/newdatabase name=None
            #     DjUrl(':newpassword@/newdatabase') -> password=newpassword name=newdatabase
            #     DjUrl(':asfcasdf23%401:/!?--atencoded') -> password=asfcasdf23@1:/! name=None port=None
            if constr.startswith(':'):
                self.password = constr.strip(':')
                constr = ''
                if encoded:
                    self.password = self.password.replace('%40', '@')
        # NOTE: constr now contains everything after @ - no engine, user, password
        # NOTE: may have port but no db ex: @:8080
        pos = constr.find('/')
        if pos > -1:
            hoststr = constr[:pos].strip()
            self.name = constr[pos + len('/'):].strip() or None
        else:
            hoststr = constr
        # all that is left is hoststr
        pos = hoststr.find(':')
        if pos > -1:
            self.host = hoststr[:pos].strip() or None
            self.port = hoststr[pos + len(':'):].strip() or None
            if self.port:
                self.port = to_int(self.port, default=None, none_to_default=False)
        elif len(hoststr) > 0:
            self.host = hoststr

#
    def from_dict(self, properties_dict: dict):
        """
        overrides instance properties with dictionary values
        NOTE: rule is that we expect the instance propery to be attribute uppercased
        EX: self.name = properties_dict[self.name.upper()]

        :param properties_dict: dictionary values
        :return: this instance for chaining. ex: x = DjUrl().from_dict({"ENGINE": "test"})
        """
        if isinstance(properties_dict, dict):
            for attr, value in vars(DjUrl).items():
                if not attr.startswith('__') and not callable(value) and not attr.startswith('_'):
                    setattr(self, attr, properties_dict.get(attr.upper(), value))
        return self

    def to_dict(self) -> dict:
        """
        converts instance properties to dictionary values
        NOTE: does not convert None values

        :return: dict of values in upper case for replacement in django databases settings
        """
        dct = {}
        for attr, value in vars(DjUrl).items():
            if not attr.startswith('__') and not callable(value) and not attr.startswith('_'):
                if getattr(self, attr) is not None:
                    dct[attr.upper()] = getattr(self, attr)
        return dct

    def __str__(self) -> str:
        url = f"{self.engine or ''}://"
        if self.user:
            url += self.user
        if self.password:
            url += f":{to_mask(self.password)}"
        url += f"@{self.host or ''}"
        if self.port:
            url += f":{self.port}"
        if self.name:
            url += f"/{self.name}"
        return url


if __name__ == "__main__":
    # test_uri = "http://localhost:8000/test1/?id=1&x=2"
    # parsed_url = ParsedUrl(test_uri)
    # print(f"root domain [{test_uri}]: {parsed_url.get_root_domain()}")
    # print(f"url:{parsed_url.url}")
    test_uri = "/?id=1&b=&c=3"
    parsed_url = ParsedUrl(test_uri, default_netloc='ex.org')
    print(f"root domain [{test_uri}]: {parsed_url.root_domain}")
    print(f"url:{parsed_url.url}")
    print(f"base: {parsed_url.base}")
    print(f"rel: {parsed_url.rel}")
    # print(f"url after base: {parsed_url.url}")
    # parsed_url.domain = "ex.org"
    # print(f"root domain [{str(parsed_url)}]: {parsed_url.root_domain}")
    # test_uri = "ex.org/"
    # print(f"root domain [{test_uri}]: {ParsedUrl(test_uri).root_domain}")
    # test_uri = "http://www.ex.org/go/"
    # print(f"root domain [{test_uri}]: {ParsedUrl(test_uri).root_domain}")
    # test_uri = "http://store.ex.org/go/"
    # print(f"root domain [{test_uri}]: {ParsedUrl(test_uri).root_domain}")
    # test_uri = "1.png"
    # print(f"test parent fragment only: {ParsedUrl(test_uri, default_netloc='localhost:8000', default_scheme='http', default_path='/mdb/')}")
    # test_uri = "#testproduct"
    # print(f"test parent fragment only: {ParsedUrl(test_uri, default_netloc='localhost:8000', default_scheme='http', default_path='/mdb/')}")
    # test_uri = "/products/"
    # purl = ParsedUrl(test_uri, default_scheme='http', default_netloc='localhost:8000', default_filepath='/blog')
    # print(purl)
    # test_uri = "../products/"
    # purl = ParsedUrl(test_uri, default_scheme='http', default_netloc='localhost:8000', default_filepath='/')
    # print(purl)
    # # test mailto links
    test_uri = 'mailto:me@mail.com?subject=mysubject&body=mybody'
    purl = ParsedUrl(test_uri, default_scheme='http', default_netloc='localhost:8000')
    print(purl)