from widget import *

log = logging.getLogger("wooly.page")
strings = StringCatalog(__file__)

class Page(Frame):
    xml_content_type = "text/xml"
    html_content_type = "text/html"
    xhtml_content_type = "application/xhtml+xml"
    xml_1_0_declaration = """<?xml version="1.0" encoding="UTF-8"?>"""
    xhtml_1_1_doctype = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">"""
    html_doctype = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">"""
    xhtml_namespace = "http://www.w3.org/1999/xhtml"

    def __init__(self, app, name):
        super(Page, self).__init__(app, name)

        self.page_html_class = None

        self.page_widgets = list()
        self.page_widgets_by_path = dict()

        self.page_parameters = list()
        self.page_parameters_by_path = dict()

        self.redirect = Attribute(app, "redirect")
        self.add_attribute(self.redirect)

        self.error = Attribute(app, "error")
        self.add_attribute(self.error)

        # XXX should this be on app instead?
        self.profile = self.ProfileAttribute(app, "profile")
        self.add_attribute(self.profile)

    def init_computed_values(self):
        self.ancestors = ()
        self.path = ""
        self.page = self
        self.frame = self

        if not self.html_class:
            self.init_html_class()

    def init_widget(self, widget):
        assert not self.sealed
        assert isinstance(widget, Widget)

        self.page_widgets.append(widget)
        self.page_widgets_by_path[widget.path] = widget

    def init_parameter(self, param):
        assert not self.sealed
        assert isinstance(param, Parameter)

        self.page_parameters.append(param)
        self.page_parameters_by_path[param.path] = param

    def get_page_parameter_by_path(self, path):
        return self.page_parameters_by_path.get(path)

    def get_page_parameters(self, session):
        return self.page_parameters

    def get_last_modified(self, session):
        return None

    def get_content_type(self, session):
        raise Exception("Not implemented")

    def get_extra_headers(self, session):
        return []

    def get_cache_control(self, session):
        return None

    def get_resource_prefix(self, session):
        return "resource?name="

    def show(self, session):
        pass

    def save_session(self, session):
        pass

    def enable_update(self, session, widget):
        pass

    def service(self, session):
        self.process(session)

        redirect = self.redirect.get(session)
        if redirect:
            raise PageRedirect()

        rend = self.render(session)

        redirect = self.redirect.get(session)
        if redirect:
            raise PageRedirect()

        return rend

    def service_error(self, session):
        # Well, we can have other handled exceptions pop up before
        # we actually get to the render so we want to record here
        # what the root cause was.
        cls, value, traceback = sys.exc_info()
        self.error.set(session, PageError(self, session, 
                                          cls, value, traceback))

        return self.render(session)

    def render_id(self, session):
        return self.name

    def render_content(self, session):
        if self.error.get(session):
            return self.render_error(session)

        return super(Page, self).render_content(session)

    def render_error(self, session):
        return self.error.get(session).render()

    class ProfileAttribute(Attribute):
        def get_default(self, session):
            return PageProfile(self)

class PageRedirect(Exception):
    pass

class UpdateRedirect(Exception):
    def __init__(self, url):
        self.url = url

class PageError(object):
    def __init__(self, page, session, cls, value, traceback):
        self.page = page
        self.session = session
        self.cls = cls
        self.value = value
        self.traceback = traceback

    def render(self):
        writer = Writer()
        writer.write("APPLICATION ERROR\n\n")

        print_exception(self.cls, self.value, self.traceback, None, writer)

        writer.write("\n")

        profile = self.page.profile.get(self.session)

        if profile:
            writer.write("Widget trace:\n\n")
            profile.print_stack_trace(writer)
            writer.write("\n")

        self.print_messages(writer)
        self.print_session(writer)

        env = self.session.request_environment

        if env:
            self.print_url_vars(env["QUERY_STRING"], writer)
            self.print_environment(env, writer)

        return "<pre>%s</pre>" % xml_escape(writer.to_string())

    def print_messages(self, writer):
        writer.write("Messages:\n\n")

        for message in self.session.messages:
            writer.write("  %s\n" % message)

        writer.write("\n")

    def print_session(self, writer):
        writer.write("Session:\n\n")

        for path in sorted(self.session.values_by_path):
            value = self.session.values_by_path[path]

            writer.write("  %-30s  %s\n" % (path, value))

        writer.write("\n")

    def print_url_vars(self, query, writer):
        writer.write("URL variables:\n\n")

        if query:
            vars = query.split(";")

            for var in sorted(vars):
                try:
                    key, value = var.split("=")
                except ValueError:
                    continue

                writer.write("  %-30s  %s\n" % (key, value))

        writer.write("\n")

    def print_environment(self, env, writer):
        writer.write("Environment:\n\n")

        for key in sorted(env):
            value = env[key]

            writer.write("  %-30s  %s\n" % (key, value))

        writer.write("\n")
