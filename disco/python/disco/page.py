#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

"""
Classes for defining L{Pages<Page>}

@sort: Page, PageRequest, PageRequestError, PageRequestErrorMessage
"""

from .application import *

_log = logger("disco.page")
_strings = StringCatalog(__file__)

# Topics
#
# - process, render
# - parameters and render_${param}_form_inputs, _errors methods
# - relation to frame and request
# - get_title, get_href
# - page nav items
#
class Page(RenderObject):
    """Generate an HTML page

    Page instances are children of a L{PageFrame}.  Pages hold
    L{Parameters<Parameter>}.

    :ivar Frame frame: The parent frame
    :ivar basestring name: The page name
    :ivar Application app: The application this page belongs to
    :ivar list parameters: A list of parameters in creation order
    :ivar dict parameters_by_name: A dictionary of parameters by name
    :ivar RenderTemplate body_template: The template that generates
    the HTML body element
    :ivar RenderTemplate content_template: The template that generates
    the interior page content

    @group Setup: delete
    @group Page attributes: get_title, get_href, get_content_type,
    get_page_navigation_items
    @group Request processing: receive_request, process*, do_process,
    load_parameters, validate_parameters

    @undocumented: __repr__

    """

    def __init__(self, frame, name):
        """
        Create a page
        """

        super().__init__()

        self._frame = frame
        self._name = name

        self.body_template = RenderTemplate(self, "body")
        self.content_template = RenderTemplate(self, "content")

        self.parameters = list()
        self.parameters_by_name = dict()

        self.widgets = list()
        self.widgets_by_name = dict()

        assert not self.app._initialized
        assert self.name not in self.frame.pages_by_name

        self.frame.pages.append(self)
        self.frame.pages_by_name[self.name] = self

    @property
    def frame(self):
        return self._frame

    @property
    def name(self):
        return self._name

    @property
    def app(self):
        return self.frame.app

    def delete(self):
        """
        Delete the page
        """

        self.frame.pages.remove(self)
        del self.frame.pages_by_name[self.name]

    def init(self):
        """
        Initialize the page
        """

        super().init()

        for param in self.parameters:
            param.init()

        for widget in self.widgets:
            widget.init()

        self.bind_templates()

    def get_content_type(self, request):
        """
        Get the value for the HTTP C{Content-Type} header

        By default it returns C{"application/xhtml+xml; charset=utf-8"}.

        @rtype: basestring
        @return: The content type
        """

        return "application/xhtml+xml; charset=utf-8"

    def get_title(self, request):
        """
        Get the page title

        @rtype: basestring
        @return: The title
        """

        return None

    def get_href(self, request):
        """
        Get the href for this page

        @rtype: basestring
        @return: The href
        """

        return "{}/{}".format(self.frame.get_href(request), self.name)

    def receive_request(self, request):
        """
        Process and render a page request and respond with the page
        content

        The internal sequence is the following:

         - Call L{Application.process} on L{app}
         - Call L{PageFrame.process} on L{frame}
         - Call L{process}
         - Call L{render}
         - Call L{ApplicationRequest.respond_ok} on L{request} and return the
           rendered content

        Any of the C{process} methods can stop further execution and
        trigger a redirect.

        @type request: L{ApplicationRequest}
        @param request: The incoming request

        @rtype: iterable<basestring>
        @return: The rendered page content
        """

        request._load_page(self)

        redirect = self.app.process(request)
        if redirect is not None:
            return app_request.respond_redirect(redirect)

        redirect = self.frame.process(request)
        if redirect is not None:
            return app_request.respond_redirect(redirect)

        redirect = self.process(request)
        if redirect is not None:
            return app_request.respond_redirect(redirect)

        content = self.render(request)
        content_type = self.get_content_type(request)

        content = content.encode("utf-8")
        
        return request.respond_ok(content, content_type)

    def process(self, request):
        """
        Processing logic executed before the page is rendered

        This internally calls L{load_parameters} and L{validate_parameters}.
        If there are any errors after either call, a L{PageRequestError}
        is raised.

        Note that forms implement page processing L{somewhat
        differently<FormPage.process>}.

        @see: L{Page.receive_request}

        @raise PageRequestError: On any errors encountered

        @rtype: basestring
        @return: A redirect URI or None
        """

        _log.debug("Processing %s", self)

        self.load_parameters(request)
        request.check_errors()
        self.validate_parameters(request)
        request.check_errors()

        redirect = self.do_process(request)
        request.check_errors()
        return redirect

    def do_process(self, request):
        """
        A standard extension point for processing

        This is called from L{process} after loading and validating
        parameters.

        @rtype: basestring
        @return: A redirect URI or None
        """

        return None

    def load_parameters(self, request):
        """
        Load parameter values from the request

        This loads raw string values from the request and converts them to 
        native Python parameter values.

        It calls L{Parameter.load} for each parameter in
        L{parameters}.
        """

        for param in self.parameters:
            param.load(request)

    def validate_parameters(self, request):
        """
        Check for invalid parameter values and accumulate
        any errors

        This calls L{Parameter.validate} for each parameter in
        L{parameters}.
        """

        for param in self.parameters:
            param.validate(request)

    @xml
    def render_title(self, request):
        """
        Render the value of L{get_title}

        @rtype: basestring
        @return: The title
        """

        return xml_escape(self.get_title(request))

    @xml
    def render_title_without_tags(self, request):
        """
        Render the value of L{get_title} with any HTML tags stripped out

        @rtype: basestring
        @return: The title with any tags removed
        """

        return strip_tags(self.render_title(request))

    # @returns tuples of (title, href)
    def get_page_navigation_items(self, request):
        """
        Get titles and hrefs for links to this page and its ancestors

        This is a data source for L{render_page_navigation}.  Each item
        is a tuple of a title (index 0) and an href (index 1), for use in
        generating HTML links.

        @rtype: iterable<tuple<basestring, basestring>>
        @return: A list of title-href pairs
        """

        items = list()

        title = self.app.get_title(request)
        href = self.app.get_href(request)
        items.append((title, href))

        if self.frame is not self.app.default_frame:
            title = self.frame.get_title(request)
            href = self.frame.get_href(request)
            items.append((title, href))

        if self is not self.frame.default_page:
            title = self.get_title(request)
            href = self.get_href(request)
            items.append((title, href))

        return items

    @xml
    def render_page_navigation(self, request):
        """
        Generate navigation links for this page in context

        This internally calls L{get_page_navigation_items}.

        @rtype: basestring
        @return: An HTML list of links with ID "page-navigation"
        """

        items = self.get_page_navigation_items(request)

        out = list()
        out.append(html_open("ul", id="page-navigation"))

        for item in items:
            title = xml_escape(item[0])
            href = item[1]
            out.append(html_li(html_link(title, href)))

        out.append(html_close("ul"))
        return "".join(out)

    @xml
    def render_account_navigation(self, request):
        """
        Generate navigation links for user login, logout, and account

        @rtype: basestring
        @return: An HTML list of links with ID "account-navigation"
        """

        if self.app.account_frame is None:
            return

        account = request.session.account

        out = list()
        out.append(html_open("ul", id="account-navigation"))

        if account is None:
            page = self.app.account_frame.create_page
            title = xml_escape(page.get_title(request))
            href = page.get_href(request)
            out.append(html_li(html_link(title, href)))

            page = self.app.account_frame.login_page
            title = xml_escape(page.get_title(request))
            href = page.get_href(request)
            out.append(html_li(html_link(title, href)))
        else:
            greeting = "Hi, {}".format(xml_escape(account.name))
            out.append(html_li(html_span(greeting, id="account-greeting")))

            frame = self.app.account_frame
            title = xml_escape(frame.get_title(request))
            href = frame.get_href(request)
            out.append(html_li(html_link(title, href)))

            page = frame.logout_page
            title = xml_escape(page.get_title(request))
            href = page.get_href(request)
            out.append(html_li(html_link(title, href)))

        out.append(html_close("ul"))
        return "".join(out)

    @xml
    def render_result_message(self, request):
        """
        Generate a notification for an operation from a previous request

        This internally uses L{Session.result_message}.

        @rtype: basestring
        @return: An HTML div with ID "result-message"
        """

        if request.session.result_message is None:
            return

        msg = xml_escape(request.session.result_message)

        return html_div(msg, id="result-message")

    def render_content(self, request):
        """
        An extension point for application-specific content

        By default it produces no content.

        @rtype: basestring
        @return: Page content
        """

        return None

    def __repr__(self):
        return fmt_repr(self, self.frame.name, self.name)

from .parameter import *
