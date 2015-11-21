from ptolemy.common.web import *

import string

log = logging.getLogger("wicket")

class WicketApplication(WebServer):
    def __init__(self):
        super(WicketApplication, self).__init__("0.0.0.0", 8080) # XXX

        self.pages_by_name = dict()

        self.html_page_template = _default_html_page_template

    def get_page(self, env):
        name = env["PATH_INFO"][1:]
        return self.pages_by_name.get(name)

    def service_request(self, env, response):
        log.info("Request %s %s", env["REQUEST_METHOD"], env["REQUEST_URI"])

        page = self.get_page(env)

        if page:
            session = WicketSession(env)

            page.process(session)
            # XXX maybe redirect
            content = page.render(session)

            content_type = page.get_content_type(session)
            content_length = str(len(content))

            headers = (("Content-Type", content_type),
                       ("Content-Length", content_length))
            
            status = "200 Just Great"
        else:
            status = "404 Not Found"
            headers = ()
            content = ""

        response(status, headers)

        log.info("Response %s", status)

        if headers:
            log.debug("Response headers:")

            for header in headers:
                log.debug("  %-24s  %s", *header)

        return (content,)

    def xxx_service_request(self, env, response):
        log.info("Servicing request %s", env['PATH_INFO'])

        headers = list()
        #headers.append(("Content-Length", str(len(content))))
        headers.append(("Content-Type", "text/event-stream"))

        response("200 OK", headers)

        def gen():
            while True:
                time.sleep(1)
                yield "stuff: " + str(time.time()) + "\n\n"

        return gen()

class WicketPage(object):
    def __init__(self, app):
        self.app = app

    def process(self, session):
        pass

    def render(self, session):
        raise Exception()

    def get_content_type(self, session):
        raise Exception()

class WicketSession(dict):
    def __init__(self, env):
        self.env = env

    def __getattr__(self, name, default=None):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

class HtmlPage(WicketPage):
    def __init__(self, app):
        super(HtmlPage, self).__init__(app)

        self.template = string.Template(self.app.html_page_template)

    @classmethod
    def get_link(cls, arg):
        href = cls.get_href(arg)
        title = cls.get_title(arg)
        return html_link(href, title)

    def get_content_type(self, session):
        return "application/xhtml+xml; charset=utf-8"

    def render(self, session):
        args = dict()

        args["title"] = self.render_title(session)
        args["navigation"] = self.render_navigation(session)
        args["content"] = self.render_content(session)

        return self.template.substitute(args)

    def render_title(self, session):
        raise Exception()

    def render_navigation(self, session):
        raise Exception()

    def render_content(self, session):
        raise Exception()

class ResourcePage(WicketPage):
    def __init__(self, app, resources_path):
        super(ResourcePage, self).__init__(app)

        self.resources_path = resources_path

    def process(self, session):
        session.resource_name = session.env["QUERY_STRING"]

    def get_content_type(self, session):
        if session.resource_name.endswith(".css"):
            return "text/css"

        return "text/plain"

    def read_file(self, path):
        file = open(path)
        try:
            return file.read()
        finally:
            file.close()

    def render(self, session):
        path = os.path.join(self.resources_path, session.resource_name)
        return self.read_file(path) # XXX alert!

def html_link(href, text=None):
    if text is None:
        text = href

    args = href, text
    return "<a href=\"%s\">%s</a>" % args

def html_list(items):
    return "<ul><li>%s</li></ul>" % "</li><li>".join(items)

def html_section(content, title=None):
    elems = list()

    if title:
        elems.append("<h2>%s</h2>" % title)

    elems.append("<div class=\"section\">%s</div>" % content)

    return "".join(elems)

_default_html_page_template = \
"""<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>${title}</title>
  </head>
  <body>
    <h1>${title}</h1>
    ${content}
  </body>
</html>"""
