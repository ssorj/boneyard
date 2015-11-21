from parameters import ListParameter
from util import *
from widgets import *
from wooly import *

strings = StringCatalog(__file__)

class WidgetPage(Page):
    def __init__(self, app, name):
        super(WidgetPage, self).__init__(app, name)

        self.widget_classes = set()

        self.page_frame = self.FrameParameter(app, "frame")
        self.add_parameter(self.page_frame)

        self.set_default_frame(self)

        self.__saved_params = dict()

    def init_widget(self, widget):
        super(WidgetPage, self).init_widget(widget)

        for cls in widget.__class__.__mro__:
            self.widget_classes.add(cls)

            if cls is Widget:
                break

    def set_frame(self, session, frame):
        self.page_frame.set(session, frame)
        return frame

    def get_frame(self, session):
        return self.page_frame.get(session)

    def pop_frame(self, session):
        frame = self.get_frame(session)
        self.set_frame(session, frame.frame)
        return frame

    def set_default_frame(self, frame):
        self.page_frame.default = frame

    def get_page_parameters(self, session):
        """
        Gets a list of parameters saved for this page and its current
        frame.

        This, combined with [gs]et_current_frame, serves to discard
        state that is out of scope.  The current pattern is to
        preserve the state of parameters in the current frame and all
        of its ancestor frames.
        """

        frame = self.get_frame(session)

        try:
            params = self.__saved_params[frame]
        except KeyError:
            params = list()
            self.save_parameters(session, params)
            self.__saved_params[frame] = params

        return params

    class FrameParameter(Parameter):
        def do_marshal(self, frame):
            return frame.path

        def do_unmarshal(self, path):
            return self.widget.page.page_widgets_by_path.get(path)

class HtmlPage(WidgetPage):
    def __init__(self, app, name):
        super(HtmlPage, self).__init__(app, name)

        self.base_name = os.path.splitext(name)[0]

        self.updates = self.UpdatesAttribute(app, "updates")
        self.add_attribute(self.updates)

        self.defers = self.UpdatesAttribute(app, "defers")
        self.add_attribute(self.defers)

        self.update_script = UpdateScript(app, "update_script", self)
        self.add_child(self.update_script)

        messages = HtmlPageMessageSet(app, "messages")
        self.add_child(messages)

        self.update_page = UpdatePage(app, self.base_name + ".update", self)
        self.app.add_page(self.update_page)

        self.popup_page = PopupPage(app, self.base_name + ".popup", self)
        self.app.add_page(self.popup_page)

        self.css_page = CssPage(app, self.base_name + ".css", self)
        self.app.add_page(self.css_page)

        self.javascript_page = JavascriptPage \
            (app, self.base_name + ".js", self)
        self.app.add_page(self.javascript_page)

    def get_content_type(self, session):
        return self.xhtml_content_type

    def enable_update(self, session, widget):
        #print "Enabling update on widget %s" % widget

        self.updates.get(session).append(widget)

    def get_update_url(self, session, widgets):
        sess = Session(self.page.update_page)

        self.page.update_page.widgets.set(sess, widgets)
        self.page.update_page.session.set(sess, session)

        return sess.marshal()

    def get_popup_url(self, session, widget):
        sess = Session(self.page.popup_page)

        self.page.popup_page.widgets.set(sess, [widget])
        self.page.popup_page.session.set(sess, session)

        return sess.marshal()

    def redirect_on_not_authorized(self, session):
        mainpage = self.app.mainpage_cb(session)
        if mainpage in self.app.pages_by_name:
            log.debug("Not authorized, redirecting to %s", mainpage)
            page = self.app.pages_by_name[mainpage]
            sess = Session(page)
            self.redirect.set(session, sess.marshal())

    def do_process(self, session):
        self.update_script.process(session)
        super(HtmlPage, self).do_process(session)

    def render_base_name(self, session):
        return self.base_name
    
    # The next 3 methods we look to enforce the hidden config option to force
    # the html content type.  This is used to make cumin compatible
    # with selenium (a workaround for selenium bug).  Ideally, someday
    # we can return to xhtml
    def render_xml_declaration(self, session):
        return self.xml_1_0_declaration
        
    def render_html_namespace(self, session):
        return """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-US">"""
    
    def render_doctype(self, session):
        return self.xhtml_1_1_doctype

    class UpdatesAttribute(Attribute):
        def get_default(self, session):
            return list()

class HtmlPageMessageSet(ItemSet):
    def __init__(self, app, name):
        item_widget = HtmlPageMessageWidget(app, "item")
        super(HtmlPageMessageSet, self).__init__(app, name, item_widget)

    def do_get_items(self, session):
        return session.messages

class HtmlPageMessageWidget(ItemWidget):
    pass

class AjaxScript(Widget):
    def __init__(self, app, name, html_page):
        super(AjaxScript, self).__init__(app, name)

        self.html_page = html_page
        try:
            self.interval = app.update_interval * 1000
        except AttributeError:
            self.interval = 10000

    def do_render(self, session):
        if self.get_widget_list(session):
            return super(AjaxScript, self).do_render(session)

    def render_url(self, session):
        widgets = self.get_widget_list(session)
        return self.html_page.get_update_url(session, widgets)

    def get_widget_list(self, session):
        pass

    def render_interval(self, session):
        return self.interval

class UpdateScript(AjaxScript):
    def get_widget_list(self, session):
        return self.html_page.updates.get(session)

class UpdatePage(Page):
    def __init__(self, app, name, html_page):
        super(UpdatePage, self).__init__(app, name)

        self.widget_tmpl = WidgetTemplate(self, "widget_html")

        self.html_page = html_page

        self.session = self.SessionParameter(app, "session")
        self.add_parameter(self.session)

        item = self.WidgetParameter(app, "item", self.html_page)

        self.widgets = ListParameter(app, "widget", item)
        self.add_parameter(self.widgets)

    def get_content_type(self, session):
        return self.xml_content_type

    def get_cache_control(self, session):
        return "no-cache"

    def do_process(self, session):
        # get the session for the main page
        sess = self.session.get(session)

        # Allow object frames to have None as an object
        # during the process pass.
        self.allow_object_not_found.set(sess, True)

        self.html_page.process(sess)
        # if the main page set its redirect attribute in its session
        redirect = self.html_page.redirect.get(sess)
        # pass that redirect on to the the update page
        if redirect:
            self.redirect.set(session, redirect)

    def service(self, session):
        self.process(session)

        # Skip the render if a redirect has been set
        if not self.redirect.get(session):
            res = self.render(session)
        # Check for a redirect from either process or render
        url = self.redirect.get(session)
        if url:
            # Send the url to the ajax script in the update response
            raise UpdateRedirect(url)
        return res

    def render_widgets(self, session):
        writer = Writer()
        sess = self.session.get(session)

        widgets = self.widgets.get(session)

        for widget in widgets:
            self.widget_tmpl.render(writer, sess, widget)
            # If a widget generated a redirect url,
            # there is no sense finishing the render
            redirect = self.redirect.get(sess)
            if redirect:
                self.redirect.set(session, redirect)
                break
        return writer.to_string()

    def render_widget_id(self, session, widget):
        return widget.path

    def render_widget(self, session, widget):
        return widget.render(session)

    class SessionParameter(Parameter):
        def do_marshal(self, session):
            return session.marshal()

        def do_unmarshal(self, string):
            return Session.unmarshal(self.app, string)

        def get(self, session):
            sess = super(UpdatePage.SessionParameter, self).get(session)

            sess.client_session = session.client_session
            sess.background = True

            return sess

    class WidgetParameter(Parameter):
        def __init__(self, app, name, page):
            self.page = page

        def do_marshal(self, widget):
            return widget.path

        def do_unmarshal(self, path):
            return self.page.page_widgets_by_path.get(path)

class PopupPage(UpdatePage):
    def get_content_type(self, session):
        return self.html_content_type

class CssPage(Page):
    def __init__(self, app, name, html_page):
        super(CssPage, self).__init__(app, name)

        self.html_page = html_page
        self.__then = datetime.utcnow()
        self.__css = None
        self.check_login = False

    def get_last_modified(self, session):
        return self.__then

    def get_content_type(self, session):
        return "text/css"

    def get_cache_control(self, session):
        return "max-age=86400"

    def get_css(self):
        if not self.__css:
            writer = Writer()

            for cls in sorted(self.html_page.widget_classes):
                strs = cls.get_module_strings()

                if strs:
                    css = strs.get(cls.__name__ + ".css")

                    if css:
                        writer.write("/** %s.%s **/\r\n" % \
                                         (cls.__module__, cls.__name__))
                        writer.write("\r\n")
                        writer.write(css)
                        writer.write("\r\n")
                        writer.write("\r\n")

            self.__css = writer.to_string()

        return self.__css

    def do_render(self, session):
        return self.get_css()

class JavascriptPage(Page):
    def __init__(self, app, name, html_page):
        super(JavascriptPage, self).__init__(app, name)

        self.html_page = html_page
        self.__then = datetime.utcnow()
        self.__javascript = None

    def get_last_modified(self, session):
        return self.__then

    def get_content_type(self, session):
        return "text/javascript"

    def get_cache_control(self, session):
        return "max-age=86400"

    def get_javascript(self):
        if not self.__javascript:
            writer = Writer()

            for cls in sorted(self.html_page.widget_classes):
                strs = cls.get_module_strings()

                if strs:
                    javascript = strs.get(cls.__name__ + ".javascript")

                    if javascript:
                        writer.write("/** %s.%s **/\r\n" % \
                                         (cls.__module__, cls.__name__))
                        writer.write("\r\n")
                        writer.write(javascript)
                        writer.write("\r\n")
                        writer.write("\r\n")

            self.__javascript = writer.to_string()

        return self.__javascript

    def do_render(self, session):
        return self.get_javascript()

class CsvPage(WidgetPage):
    def get_content_type(self, session):
        return "text/csv"

    def get_file_name(self, session):
        return "cumin.csv"

    def get_extra_headers(self, session):
        file_name = self.get_file_name(session)
        return [('Content-Disposition', "attachment; filename=\"%s\"" % file_name), 
                ("Content-description", "File Transfer")]

    def do_render(self, session):
        csv = self.render_content(session)
        return csv and csv or " "
