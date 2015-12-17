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

from .application import *

import traceback as _traceback

from urllib.parse import parse_qs as _parse_qs

_log = logger("disco.request")
_strings = StringCatalog(__file__)

class Request:
    """
    The state of one L{Application} request and methods for sending a
    response

     - It is created once for each call to L{Application.receive_request}
     - It accumulates output headers for the response
     - It keeps L{Parameter} state and exposes it via L{Parameter.get}
       and L{.set<Parameter.set>}
     - It collects L{PageRequestErrorMessages<PageRequestErrorMessage>} and
       L{ParameterErrorMessages<ParameterErrorMessage>}

    Application variables can be added by assigning to a new
    attribute on L{.attributes}::

        def process(self, request):
            request.attributes.somename = "somevalue"

        def render(self, request):
            return request.attributes.somename

    @type path: iterable<basestring>
    @ivar path: Preparsed elements of the requested path (PATH_INFO)

    @type method: basestring
    @ivar method: The HTTP request method (GET, POST, etc.)

    @type page: L{Page}
    @ivar page: The page for which this request was created

    @type session: L{Session}
    @ivar session: The client session

    @type attributes: L{AttributeObject}
    @ivar attributes: Arbitrary request-scoped application variables

    @type errors: iterable<L{PageRequestErrorMessage}>
    @ivar errors: The error messages

    @group Response generation: add_response_header, respond_*

    @undocumented: __init__, __repr__
    """

    def __init__(self, app, env, start_response, parent=None):
        self._app = app
        self._env = env
        self._start_response = start_response
        self._parent = parent

        self._path = None
        self._session = None
        self._response_headers = list()
        self._errors = list()
        self._attributes = AttributeDict()

        self._page = None
        self._parameter_values_by_parameter = dict()

        if self._parent is not None:
            self._page = self._parent.page

    @property
    def app(self):
        return self._app

    @property
    def path(self):
        return self._path

    @property
    def page(self):
        return self._page

    @property
    def session(self):
        return self._session

    @property
    def attributes(self):
        return self._attributes

    @property
    def errors(self):
        return self._errors

    @property
    def method(self):
        return self._env["REQUEST_METHOD"]

    def _load(self):
        self._load_path()
        self._load_session()

    def _load_path(self):
        path = self._env["PATH_INFO"]
        path = path[1:].split("/")
        path = [url_unescape(x) for x in path]

        self._path = path

    # This sets the client session cookie if it isn't already there
    def _load_session(self):
        session_id = self._parse_session_cookie()

        if session_id is None:
            self._session = Session(self.app, self)
        else:
            try:
                self._session = self.app._sessions_by_id[session_id]
            except KeyError:
                self._session = Session(self.app, self)

        self.session._touch()

    def _parse_session_cookie(self):
        try:
            cookie_string = self._env["HTTP_COOKIE"]
        except KeyError:
            return

        for crumb in cookie_string.split(";"):
            name, value = crumb.split("=", 1)
            name = name.strip()
            
            if name == "session":
                return value.strip()

    def _load_page(self, page):
        self._page = page
        self._load_parameter_values()

    def _load_parameter_values(self):
        query_vars = self._parse_query_string()

        for param in self.page.parameters:
            strings = query_vars.get(param.name)
            _ParameterValue(self, param, strings)

        input_names = set(query_vars)
        expected_names = self.page.parameters_by_name
        unexpected_names = input_names.difference(expected_names)

        if unexpected_names:
            names = fmt_list(unexpected_names)
            msg = "Unexpected variables in query: {}".format(names)

            raise RequestError(msg)

    def _parse_query_string(self):
        query_vars = dict()
        query_string = None

        if self.method == "GET":
            query_string = self._env["QUERY_STRING"]
        elif self.method == "POST":
            content_type = self._env["CONTENT_TYPE"]

            assert content_type == "application/x-www-form-urlencoded"

            length = int(self._env["CONTENT_LENGTH"])
            query_string = self._env["wsgi.input"].read(length)

        if not query_string:
            return query_vars

        try:
            items = _parse_qs(query_string, False, True)
        except ValueError:
            raise RequestError("Failed to parse query string")

        query_vars.update(items)

        return query_vars

    def branch(self):
        return Request \
            (self.app, self._env, self._start_response, self)

    def get_href(self):
        query_vars = list()

        for param in self.page.parameters:
            value = self._get_parameter_value(param)

            if value.object is None:
                continue

            if value.object == param.get_default_value(self):
                continue

            strings = param.marshal(self, value.object)

            for string in strings:
                args = url_escape(param.name), url_escape(string)
                query_vars.append("{}={}".format(*args))

        args = self.page.frame.name, self.page.name, ";".join(query_vars)

        return "/{}/{}?{}".format(*args)

    def _get_parameter_value(self, param):
        try:
            return self._parameter_values_by_parameter[param]
        except KeyError:
            if self._parent is None:
                return

            return self._parent._get_parameter_value(param)

    def add_response_header(self, name, value):
        """
        Add a header to the response

        @type name: basestring
        @param name: The header name

        @type value: basestring
        @param value: The header value
        """

        assert isinstance(value, str)

        self._response_headers.append((name, value))

    def add_error(self, message):
        """
        Add an error for a problem encountered during request processing

        This internally creates a L{RequestErrorMessage}.

        @type message: basestring
        @param message: The string message for the error
        """

        RequestErrorMessage(self, message)

    def check_errors(self):
        """
        Raise an exception if the request contains any errors

        @raise RequestError: If there are any errors
        """

        param_errors = list()

        for param in self.page.parameters:
            param_errors.extend(param.get_errors(self))

        if param_errors:
            count = len(param_errors)
            msg = "{} parameter {}".format(count, plural("error", count))

            self.add_error(msg)

        if self.errors:
            raise PageRequestError(self)

    def _respond(self, status, content=None, content_type=None):
        _log.info("Responding %s", status)

        if self.session is not None:
            # value = "session={}; Path=/; Secure; HttpOnly".format(self.session._id)
            value = "session={}; Path=/; HttpOnly".format(self.session._id)
            self.add_response_header("Set-Cookie", value)

        if content is None:
            self.add_response_header("Content-Length", "0")
            self._start_response(status, self._response_headers)
            return (b"",)

        assert isinstance(content, bytes), type(content)
        assert content_type is not None

        content_length = len(content)

        self.add_response_header("Content-Length", str(content_length))
        self.add_response_header("Content-Type", content_type)

        self._start_response(status, self._response_headers)

        return (content,)

    def respond_ok(self, content, content_type):
        """
        Send 200 OK

        @type content: basestring
        @param content: The response content

        @type content_type: basestring
        @param content_type: The response content MIME type

        @rtype: iterable<basestring>
        @return: The response content
        """

        return self._respond("200 OK", content, content_type)

    def respond_redirect(self, location):
        """
        Send 303 See Other

        @type location: basestring
        @param location: The target URI

        @rtype: iterable<basestring>
        @return: The response content
        """

        self.add_response_header("Location", str(location))
        return self._respond("303 See Other")

    def respond_not_modified(self):
        """
        Send 304 Not Modified

        @rtype: iterable<basestring>
        @return: The response content
        """

        return self._respond("304 Not Modified")

    def respond_not_found(self):
        """
        Send 404 Not Found

        @rtype: iterable<basestring>
        @return: The response content
        """

        error = _NotFoundError(self)
        return error.respond(self)

    def _respond_application_error(self):
        error = sys.exc_info()[1]
        return error.respond(self)

    def _respond_unexpected_error(self):
        exc = sys.exc_info()[1]
        error = _UnexpectedError(self, exc)
        return error.respond(self)

    def __repr__(self):
        return fmt_repr(self, self.method, "/".join(self.path))

class RequestError(ApplicationError):
    """
    For errors encountered while processing a request

    RequestErrors are trapped and reported during L{Application}
    request processing.

    @type request: L{Request}
    @ivar request: The request for which the error exists

    @undocumented: __init__, __repr__
    """

    def __init__(self, request):
        assert isinstance(request, Request), request

        msg = "Errors were encountered during request processing"
        super().__init__(msg)

        self.request = request

        self.template = _strings["error_message"]
        self.title = "Error!"
        self.status = "500 Internal Server Error"

    def respond(self, request):
        content = self.render(request)
        content_type = "application/xhtml+xml; charset=utf-8"

        content = content.encode("utf-8")
        
        return request._respond(self.status, content, content_type)

    def render(self, request):
        args = {
            "navigation": html_link("Home", "/"),
            "title": xml_escape(self.title),
            "summary": self.render_summary(request),
            "details": self.render_details(request),
        }

        return self.template.format(**args)

    def render_details(self, request):
        out = list()
        out.append(self.render_traceback())
        out.append(self.render_request_details(request))
        out.append(self.render_application_details(request))
        return "".join(out)

    def render_traceback(self):
        if sys.exc_info()[1] is None:
            return ""

        content = xml_escape(_traceback.format_exc())
        return self.render_detail_section("Traceback", content)

    def render_request_details(self, request):
        out = list()

        content = _fmt_dict(request._env)
        section = self.render_detail_section("WSGI environment", content)
        out.append(section)

        content = _fmt_dict(get_app_request_info(request))
        section = self.render_detail_section("Request", content)
        out.append(section)

        return "".join(out)

    def render_application_details(self, request):
        out = list()

        content = _fmt_dict(get_system_info())
        section = self.render_detail_section("System", content)
        out.append(section)

        return "".join(out)

    def render_detail_section(self, title, content):
        out = list()
        out.append(html_elem("h4", xml_escape(title)))

        if content is None:
            out.append(html_none())
        else:
            elem = html_elem("pre", content)
            out.append(html_elem("p", elem))

        return "".join(out)

    def render_summary(self, request):
        out = list()
        out.append(html_p(self.message))

        out.append(html_elem("h4", "Page errors"))

        out.append(html_open("ul"))
        
        for error in self.request.errors:
            out.append(html_li(xml_escape(error.message)))

        out.append(html_close("ul"))

        for param in self.request.page.parameters:
            out.append(self.render_parameter_errors(self.request, param))

        return "".join(out)

    def render_parameter_errors(self, request, parameter):
        errors = parameter.get_errors(request)

        if not errors:
            return ""

        name = xml_escape(parameter.name)

        out = list()
        out.append(html_elem("h4", "Parameter '{}'".format(name)))
        out.append(html_open("ul"))

        for error in errors:
            out.append(html_li(xml_escape(error.message)))

        out.append(html_close("ul"))
        return "".join(out)

    def render_details(self, request):
        out = list()
        out.append(self.render_traceback())
        out.append(self.render_request_details())
        out.append(self.render_application_details(request))
        return "".join(out)

    def render_request_details(self):
        out = list()

        content = _fmt_dict(get_request_info(self.request))
        section = self.render_detail_section("Request", content)
        out.append(section)

        content = _fmt_dict(get_session_info(self.request))
        section = self.render_detail_section("Session", content)
        out.append(section)        

        if self.request.page is not None:
            content = _fmt_dict(get_page_info(self.request.page))
            section = self.render_detail_section("Page", content)
            out.append(section)

            content = _fmt_dict(get_parameters(self.request))
            section = self.render_detail_section("Parameters", content)
            out.append(section)

        return "".join(out)

class RequestErrorMessage:
    """
    @type request: L{Request}
    @ivar request: The request for which the error exists

    @type message: basestring
    @ivar message: The error message

    @undocumented: __init__, __repr__
    """

    def __init__(self, request, message):
        assert isinstance(request, PageRequest)

        self.request = request
        self.message = message

        self.request._errors.append(self)

    def __repr__(self):
        return fmt_repr(self, self.request, self.message)

class _ParameterValue:
    def __init__(self, request, parameter, strings):
        self.request = request
        self.parameter = parameter
        self.strings = strings
        self.errors = list()
        self.object = None

        self.request._parameter_values_by_parameter[self.parameter] = self

    def __repr__(self):
        if isinstance(self.parameter, SecretParameter):
            return "[redacted]"

        default = self.parameter.get_default_value(self.request)
        args = pformat(self.object), self.strings, pformat(default)

        return "{}; strings {}; default {}".format(*args)

class _UnexpectedError(RequestError):
    def __init__(self, request, exception):
        super().__init__(request)

        self.wrapped_exception = exception

    def render_summary(self, request):
        out = list()
        out.append(html_p("Yikes! An unexpected error:"))
        out.append(html_elem("pre", xml_escape(self.message)))
        return "".join(out)

class _NotFoundError(RequestError):
    def __init__(self, request):
        super().__init__(request)

        self.title = "Not found!"
        self.status = "404 Not Found"

    def render_summary(self, request):
        path = "/".join(self.request.path)
        return "Nothing exists for path '{}'".format(xml_escape(path))

def _fmt_dict(coll):
    return xml_escape(fmt_dict(coll))

from .parameter import SecretParameter
