from util import *

log = logging.getLogger("wooly.session")

class CSRFException(Exception):
    pass

class Session(object):
    http_date_gmt = "%a, %d %b %Y %H:%M:%S GMT"

    def __init__(self, page):
        self.page = page

        self.client_session = None

        self.trunk = None

        self.values_by_path = dict()
        self.cookies_by_name = dict() # name => (newly set?, value, expires)

        self.request_environment = None

        self.messages = list()

    def branch(self):
        session = Session(self.page)
        session.trunk = self

        return session

    def log(self, message):
        self.messages.append(message)

    def get_cookie(self, name):
        try:
            return self.cookies_by_name[name][1]
        except KeyError:
            pass

    def set_cookie(self, name, value, expires=None):
        self.cookies_by_name[name] = (True, value, expires)

    def expire_cookie(self, name):
        dawn_of_time = time.gmtime(1)[0:6]
        self.set_cookie(name, "", datetime(*dawn_of_time))

    def get(self, key):
        if key in self.values_by_path:
            value = self.values_by_path[key]
        elif self.trunk:
            value = self.trunk.get(key)
        else:
            value = None

        return value

    def set(self, key, value):
        self.values_by_path[key] = value

        return value

    def unset(self, key):
        if key in self.values_by_path:
            del self.values_by_path[key]

    def marshal(self):
        page = self.page.name
        vars = self.marshal_url_vars()

        if vars:
            url = page + "?" + vars
        else:
            url = page

        if self.page.app.debug: 
            profile = self.page.profile.get(self)
            profile.urls.append(url)

        return url

    def marshal_url_vars(self, separator=";"):
        params = self.page.get_page_parameters(self)
        vars = list()

        values_by_path = self.gather_values()

        for param in params:
            key = param.path
            value = values_by_path.get(key)

            if value is not None:
                if param.is_collection:
                    for item in value:
                        sitem = quote(param.marshal(item))
                        vars.append("%s=%s" % (key, sitem))
                elif value != param.get_default(self):
                    svalue = quote(param.marshal(value))
                    vars.append("%s=%s" % (key, svalue))

        return separator.join(vars)
            
    def gather_values(self):
        if self.trunk is None:
            return self.values_by_path
        else:
            values_by_path = dict()

            values_by_path.update(self.trunk.gather_values())
            values_by_path.update(self.values_by_path)

            return values_by_path

    def unmarshal(cls, app, string):
        elems = string.split("?")

        try:
            name = elems[0]

            if name.startswith("/"):
                name = name[1:]

            page = app.pages_by_name[name]
        except KeyError:
            raise Exception("Page '%s' not found" % name)

        session = Session(page)

        try:
            session.unmarshal_url_vars(elems[1])
        except IndexError:
            pass

        return session

    unmarshal = classmethod(unmarshal)

    def unmarshal_url_vars(self, string, separator=";"):
        vars = string.split(separator)

        for var in vars:
            try:
                skey, svalue = var.split("=")
            except ValueError:
                continue

            key = unquote(skey)
            value = unquote_plus(svalue)

            param = self.page.get_page_parameter_by_path(key)

            if param:
                param.add(self, param.unmarshal(value), key)

    def marshal_cookies(self, secure_cookies):
        """
        Produce a list of strings representing cookies newly set on
        this session.

        The strings are formatted to serve as HTTP Set-Cookie header
        values.
        """

        headers = list()

        for name, record in self.cookies_by_name.iteritems():
            new, value, expires = record

            if new:
                crumbs = list()
                crumbs.append("%s=%s" % (name, value))

                if expires:
                    when = expires.strftime(self.http_date_gmt)
                    crumbs.append("expires=%s" % when)

                if secure_cookies:
                    crumbs.append("secure")

                headers.append("; ".join(crumbs))

        return headers

    def unmarshal_cookies(self, string):
        """
        Parse and load cookies from string.

        The string must be formatted as dictated by the HTTP Cookie
        header.
        """

        for crumb in string.split(";"):
            name, value = crumb.split("=", 1)
            self.cookies_by_name[name.strip()] = (False, value.strip(), None)

    def get_user(self):
        return self.client_session.attributes["login_session"].user

    def __repr__(self):
        args = self.__class__.__name__, self.trunk, self.page.app, id(self)
        return "%s(trunk=%s,app=%s,id=%i)" % args

class SessionAttribute(object):
    def __init__(self, widget, name):
        assert hasattr(widget, "app"), widget
        
        self.widget = widget
        self.name = name
        self.default = None

        self.key = (self.widget, self.name)

    def do_get(self, session):
        return copy(self.default)

    def get(self, session):
        value = session.get(self.key)

        if value is None:
            value = self.do_get(session)

            if value is not None:
                self.set(session, value)

        return value

    def add(self, session, value):
        self.set(session, value)

    def set(self, session, value):
        session.set(self.key, value)
