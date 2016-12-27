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

@sort: Page, PageSession, PageSessionError, PageErrorMessage
"""

from application import *

import urlparse as _urlparse

_log = logger("cabinet.page")
_strings = StringCatalog(__file__)

# Topics
#
# - process, render
# - parameters and render_${param}_form_inputs, _errors methods
# - relation to frame and session
# - add_error, get_errors, PageErrorMessage
# - get_title, get_href
# - page nav items
# - result message
# - client session, reset_client_session_id
# - account
#
class Page(RenderObject):
    """
    Generate an HTML page

    Page instances are children of a L{PageFrame}.  Pages hold
    L{Parameters<Parameter>}.

    @type frame: L{Frame}
    @ivar frame: The parent frame

    @type name: basestring
    @ivar name: The page name

    @type app: L{Application}
    @ivar app: The application of this page

    @type parameters: iterable<L{Parameter}>
    @ivar parameters: A list of parameters in creation order

    @type parameters_by_name: dict<basestring, L{Parameter}>
    @ivar parameters_by_name: A dictionary of parameters by parameter
    name

    @type body_template: L{RenderTemplate}
    @ivar body_template: The template that generates the HTML C{body}
    element

    @type content_template: L{RenderTemplate}
    @ivar content_template: The template that generates the interior
    page content

    @group Setup: delete
    @group Page attributes: get_title, get_href, get_content_type,
    add_error, get_errors, get_page_navigation_items
    @group Client attributes: get_client_session, reset_client_session_id,
    get_account, set_account, get_result_message, set_result_message
    @group Request processing: receive, process*, do_process,
    load_parameters, validate_parameters, check_errors

    @sort: get_account, set_account, get_result_message, set_result_message

    @undocumented: __repr__
    """

    def __init__(self, frame, name):
        """
        Create a page
        """

        super(Page, self).__init__()

        self._frame = frame
        self._name = name

        self.body_template = RenderTemplate(self, "body")
        self.content_template = RenderTemplate(self, "content")

        self.parameters = list()
        self.parameters_by_name = dict()

        assert self.app._initialized is False
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

        super(Page, self).init()

        for param in self.parameters:
            param.init()

        self.bind_templates()

    def get_content_type(self, session):
        """
        Get the value for the HTTP C{Content-Type} header

        By default it returns C{"application/xhtml+xml; charset=utf-8"}.

        @rtype: basestring
        @return: The content type
        """

        return "application/xhtml+xml; charset=utf-8"

    def get_title(self, session):
        """
        Get the page title

        @rtype: basestring
        @return: The title
        """

        return None

    def get_href(self, session):
        """
        Get the href for this page

        @rtype: basestring
        @return: The href
        """

        args = self.frame.get_href(session), self.name
        return "%s/%s" % args

    def get_client_session(self, session):
        """
        Get the client session for the client of this request

        @rtype: L{ClientSession}
        @return: The client session
        """

        return session._client_session

    def reset_client_session_id(self, session):
        """
        Reset the client session ID for the client of this request

        This is used to prevent session-fixation attacks.
        """

        prev = self.get_client_session(session)
        next = prev._copy_with_new_id()

        prev._delete()

        session._client_session = next
        session._set_client_session_cookie(next)

    def get_account(self, session):
        """
        Get the login account of the client requesting this page

        If the account exists, the account user is understood to be
        logged in.

        @rtype: L{AccountAdapter}
        @return: The login account
        """

        return self.get_client_session(session).account

    def set_account(self, session, account):
        """
        Set the login account for the client requesting this page

        @type account: L{AccountAdapter}
        @param account: The login account
        """

        self.get_client_session(session).account = account
        
    def get_result_message(self, session):
        """
        Get a message set in a previous request after some work was done

        This is typically used to show the result of a user operation.  It
        clears the message after getting it.

        @rtype: basestring
        @return: The message
        """

        client = self.get_client_session(session)
        return client.get_and_set("result_message", None)

    def set_result_message(self, session, message):
        """
        Set a message for use in a subsequent request

        This is usually called after performing a user operation.  The
        message must be cleared via L{get_result_message} before it
        can be set again.

        @type message: basestring
        @param message: The message
        """

        assert self.get_client_session(session).result_message is None
        self.get_client_session(session).result_message = message

    def get_errors(self, session):
        """
        Get the errors accumulated so far during processing of this page

        @rtype: iterable<L{PageErrorMessage}>
        @return: The error messages
        """

        return session._page_errors

    def add_error(self, session, message):
        """
        Add an error for a problem encountered during page processing

        This internally creates a L{PageErrorMessage}.

        @type message: basestring
        @param message: The string message for the error
        """

        PageErrorMessage(session, message)

    def receive(self, request):
        """
        Process and render a page request and respond with the page
        content

        The internal sequence is the following:

         - Create a L{PageSession}
         - Call L{Application.process} on L{app}
         - Call L{PageFrame.process} on L{frame}
         - Call L{process}
         - Call L{render}
         - Call L{ApplicationRequest.respond} on L{request} and return the
           rendered content

        Any of the C{process} methods can stop further execution and
        trigger a redirect.

        @type request: L{ApplicationRequest}
        @param request: The incoming request

        @rtype: iterable<basestring>
        @return: The rendered page content
        """

        session = PageSession(self, request)

        redirect = self.app.process(session)
        if redirect is not None:
            return request.send_redirect(redirect)

        redirect = self.frame.process(session)
        if redirect is not None:
            return request.send_redirect(redirect)

        redirect = self.process(session)
        if redirect is not None:
            return request.send_redirect(redirect)

        status = "200 OK"
        content = self.render(session)
        content_type = self.get_content_type(session)

        return request.respond(status, content, content_type)

    def process(self, session):
        """
        Processing logic executed before the page is rendered

        This internally calls L{load_parameters} and L{validate_parameters}.
        If there are any errors after either call, a L{PageSessionError}
        is raised.

        Note that forms implement page processing L{somewhat
        differently<FormPage.process>}.

        @see: L{Page.receive}

        @raise PageSessionError: On any errors encountered

        @rtype: basestring
        @return: A redirect URI or None
        """

        _log.debug("Processing %s", self)

        self.load_parameters(session)
        self.check_errors(session)
        self.validate_parameters(session)
        self.check_errors(session)

        redirect = self.do_process(session)

        self.check_errors(session)

        return redirect

    def check_errors(self, session):
        """
        Raise an exception if the request contains any errors

        @raise PageSessionError: If there are any errors
        """

        param_errors = list()

        for param in self.parameters:
            param_errors.extend(param.get_errors(session))

        if param_errors:
            count = len(param_errors)
            args = count, plural("error", count)
            msg = "%i parameter %s" % args

            self.add_error(session, msg)

        errors = self.get_errors(session)

        if errors:
            raise PageSessionError(session)

    def do_process(self, session):
        """
        A standard extension point for processing

        This is called from L{process} after loading and validating
        parameters.

        @rtype: basestring
        @return: A redirect URI or None
        """

        return None

    def load_parameters(self, session):
        """
        Load parameter values from the request

        This loads raw string values from the request and converts them to 
        native Python parameter values.

        It calls L{Parameter.load} for each parameter in
        L{parameters}.
        """

        for param in self.parameters:
            param.load(session)

    def validate_parameters(self, session):
        """
        Check for invalid parameter values and accumulate
        any errors

        This calls L{Parameter.validate} for each parameter in
        L{parameters}.
        """

        for param in self.parameters:
            param.validate(session)

    @xml
    def render_title(self, session):
        """
        Render the value of L{get_title}

        @rtype: basestring
        @return: The title
        """

        return xml_escape(self.get_title(session))

    @xml
    def render_title_without_tags(self, session):
        """
        Render the value of L{get_title} with any HTML tags stripped out

        @rtype: basestring
        @return: The title with any tags removed
        """

        return strip_tags(self.render_title(session))

    # @returns tuples of (title, href)
    def get_page_navigation_items(self, session):
        """
        Get titles and hrefs for links to this page and its ancestors

        This is a data source for L{render_page_navigation}.  Each item
        is a tuple of a title (index 0) and an href (index 1), for use in
        generating HTML links.

        @rtype: iterable<tuple<basestring, basestring>>
        @return: A list of title-href pairs
        """

        items = list()

        title = self.app.get_title(session)
        href = self.app.get_href(session)
        items.append((title, href))

        if self.frame is not self.app.default_frame:
            title = self.frame.get_title(session)
            href = self.frame.get_href(session)
            items.append((title, href))

        if self is not self.frame.default_page:
            title = self.get_title(session)
            href = self.get_href(session)
            items.append((title, href))

        return items

    @xml
    def render_page_navigation(self, session):
        """
        Generate navigation links for this page in context

        This internally calls L{get_page_navigation_items}.

        @rtype: basestring
        @return: An HTML list of links with ID "page-navigation"
        """

        items = self.get_page_navigation_items(session)

        out = list()
        out.append(html_open("ul", id="page-navigation"))

        for item in items:
            title = xml_escape(item[0])
            href = item[1]
            out.append(html_li(html_link(title, href)))

        out.append(html_close("ul"))
        return "".join(out)

    @xml
    def render_account_navigation(self, session):
        """
        Generate navigation links for user login, logout, and account

        @rtype: basestring
        @return: An HTML list of links with ID "account-navigation"
        """

        account = self.get_account(session)

        out = list()
        out.append(html_open("ul", id="account-navigation"))

        if account is None:
            page = self.app.account_frame.create_page
            title = xml_escape(page.get_title(session))
            href = page.get_href(session)
            out.append(html_li(html_link(title, href)))

            page = self.app.account_frame.login_page
            title = xml_escape(page.get_title(session))
            href = page.get_href(session)
            out.append(html_li(html_link(title, href)))
        else:
            greeting = "Hi, %s" % xml_escape(account.name)
            out.append(html_li(html_span(greeting, id="account-greeting")))

            frame = self.app.account_frame
            title = xml_escape(frame.get_title(session))
            href = frame.get_href(session)
            out.append(html_li(html_link(title, href)))

            page = frame.logout_page
            title = xml_escape(page.get_title(session))
            href = page.get_href(session)
            out.append(html_li(html_link(title, href)))

        out.append(html_close("ul"))
        return "".join(out)

    @xml
    def render_result_message(self, session):
        """
        Generate a notification for an operation from a previous request

        This internally calls L{get_result_message}.

        @rtype: basestring
        @return: An HTML div with ID "result-message"
        """

        msg = self.get_result_message(session)

        if msg is None:
            return

        msg = xml_escape(msg)

        return html_div(msg, id="result-message")

    def render_content(self, session):
        """
        An extension point for application-specific content

        By default it produces no content.

        @rtype: basestring
        @return: Page content
        """

        return None

    def __repr__(self):
        args = self.__class__.__name__, self.name
        return "%s(%s)" % args

class PageSession(AttributeObject):
    """
    The state of one L{Page} request and response

     - It is created once for each call to L{Page.receive}
     - It keeps L{Parameter} state and exposes it via L{Parameter.get}
       and L{.set<Parameter.set>}
     - It collects L{PageErrorMessages<PageErrorMessage>} and
       L{ParameterErrorMessages<ParameterErrorMessage>}
     - It holds arbitrary request-scoped application variables as
       attributes

    Application variables can be added by assigning to a new
    attribute::

        def process(self, session):
            session.somevar = "somevalue"

        def render(self, session):
            return session.somevar

    @type request: L{ApplicationRequest}
    @ivar request: The request for which this session was created

    @type page: L{Page}
    @ivar page: The page for which this session was created

    @undocumented: __init__, __repr__
    """

    def __init__(self, page, request):
        super(PageSession, self).__init__()

        self._page = page
        self._request = request

        self._parameter_values_by_parameter = dict()
        self._cookies_by_name = dict()
        self._client_session = None
        self._page_errors = list()

        self._load()

    @property
    def page(self):
        return self._page

    @property
    def request(self):
        return self._request

    def _load(self):
        self._load_parameter_values()
        self._load_cookies()
        self._load_client_session()

    def _load_parameter_values(self):
        request_method = self.request.method
        request_env = self.request._env

        if request_method == "GET":
            query_string = request_env["QUERY_STRING"]
        elif request_method == "POST":
            content_type = request_env["CONTENT_TYPE"]

            assert content_type == "application/x-www-form-urlencoded"

            length = int(request_env["CONTENT_LENGTH"])
            query_string = request_env["wsgi.input"].read(length)

        strings_by_name = dict()

        if query_string:
            try:
                items = _urlparse.parse_qs(query_string, False, True)
            except ValueError:
                raise ApplicationRequestError("Failed to parse query string")

            strings_by_name.update(items)

        for param in self.page.parameters:
            strings = strings_by_name.get(param.name)
            _ParameterValue(self, param, strings)

        input_names = set(strings_by_name)
        expected_names = self.page.parameters_by_name
        unexpected_names = input_names.difference(expected_names)

        if unexpected_names:
            args = fmt_list(unexpected_names)
            msg = "Unexpected variables in query: %s" % args
            self.page.add_error(self, msg)

            raise PageSessionError(self)

    def _load_cookies(self):
        try:
            cookie_string = self.request._env["HTTP_COOKIE"]
        except KeyError:
            return

        for crumb in cookie_string.split(";"):
            name, value = crumb.split("=", 1)
            _Cookie(self, name.strip(), value.strip())

    # This sets the client session cookie if it isn't already there
    def _load_client_session(self):
        try:
            id = self._cookies_by_name["session"].value
            client = self.page.app._client_sessions_by_id[id]
        except KeyError:
            client = ClientSession(self.page.app)
            self._set_client_session_cookie(client)

        client._touch()

        self._client_session = client

    def _set_client_session_cookie(self, client):
        self.request.attributes["cabinet.set-client-session"] = client

    def __repr__(self):
        args = self.__class__.__name__, self.page
        return "%s(%s)" % args

class _ParameterValue(object):
    def __init__(self, session, parameter, strings):
        self.session = session
        self.parameter = parameter
        self.strings = strings
        self.errors = list()
        self.object = None

        self.session._parameter_values_by_parameter[self.parameter] = self

    def __repr__(self):
        if isinstance(self.parameter, SecretParameter):
            return "[redacted]"

        default = self.parameter.get_default_value(self.session)
        args = pformat(self.object), self.strings, pformat(default)
        return "%s; strings %s; default %s" % args

class _Cookie(object):
    def __init__(self, session, name, value):
        self.session = session
        self.name = name
        self.value = value

        self.session._cookies_by_name[self.name] = self

    def __repr__(self):
        return self.value

class PageSessionError(ApplicationRequestError):
    """
    For L{Page} processing errors

    @type session: L{PageSession}
    @ivar session: The page session for which the error exists

    @undocumented: __init__, __repr__
    """

    def __init__(self, session):
        assert isinstance(session, PageSession)

        msg = "Errors were encountered during page processing"
        super(PageSessionError, self).__init__(msg)

        self.session = session

    def render_summary(self, request):
        out = list()
        out.append(html_p(self.message))

        out.append(html_elem("h4", "Page errors"))

        out.append(html_open("ul"))
        
        for error in self.session.page.get_errors(self.session):
            out.append(html_li(xml_escape(error.message)))

        out.append(html_close("ul"))

        for param in self.session.page.parameters:
            out.append(self.render_parameter_errors(self.session, param))

        return "".join(out)

    def render_parameter_errors(self, session, parameter):
        errors = parameter.get_errors(session)

        if not errors:
            return ""

        name = xml_escape(parameter.name)

        out = list()
        out.append(html_elem("h4", "Parameter '%s'" % name))
        out.append(html_open("ul"))

        for error in errors:
            out.append(html_li(xml_escape(error.message)))

        out.append(html_close("ul"))
        return "".join(out)

    def render_details(self, request):
        out = list()
        out.append(self.render_traceback())
        out.append(self.render_session_details())
        out.append(self.render_request_details(request))
        out.append(self.render_application_details(request))
        return "".join(out)

    def render_session_details(self):
        out = list()

        content = _fmt_dict(get_session_info(self.session))
        section = self.render_detail_section("Session", content)
        out.append(section)

        content = _fmt_dict(get_page_info(self.session.page))
        section = self.render_detail_section("Page", content)
        out.append(section)

        content = _fmt_dict(get_parameters(self.session))
        section = self.render_detail_section("Parameters", content)
        out.append(section)

        content = _fmt_dict(get_client_info(self.session))
        section = self.render_detail_section("Client", content)
        out.append(section)        

        return "".join(out)

class PageErrorMessage(object):
    """
    @type session: L{PageSession}
    @ivar session: The page session for which the error exists

    @type message: basestring
    @ivar message: The error message

    @undocumented: __init__, __repr__
    """

    def __init__(self, session, message):
        assert isinstance(session, PageSession)

        self.session = session
        self.message = message

        self.session._page_errors.append(self)

    def __repr__(self):
        args = self.__class__.__name__, self.session, self.message
        return "%s(%s,%s)" % args

def _fmt_dict(coll):
    return xml_escape(fmt_dict(coll))

from parameter import *
