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

_log = logger("turret.request")

class Request:
    """
    The state of one L{Application} request and methods for sending a
    response

     - It is created once for each call to L{Application.receive_request}
     - It accumulates output headers for the response
     - It keeps L{Parameter} state and exposes it via L{Parameter.get}
       and L{.set<Parameter.set>}
     - It collects L{RequestErrorMessages<RequestErrorMessage>} and
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

    @type session: L{Session}
    @ivar session: The client session

    @type attributes: L{AttributeObject}
    @ivar attributes: Arbitrary request-scoped application variables

    @type errors: iterable<L{RequestErrorMessage}>
    @ivar errors: The error messages

    @group Response generation: add_response_header, respond_*

    @undocumented: __init__, __repr__
    """

    def __init__(self, app, env, start_response):
        self._app = app
        self._env = env
        self._start_response = start_response

        self._path = None
        self._session = None
        self._response_headers = list()
        self._errors = list()
        self._attributes = AttributeDict()

        self._parameter_values_by_parameter = dict()

    @property
    def app(self):
        return self._app

    @property
    def path(self):
        return self._path

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

    def _load_parameter_values(self, procedure):
        query_vars = self._parse_query_string()

        for param in procedure.parameters:
            strings = query_vars.get(param.name)
            _ParameterValue(self, param, strings)

        input_names = set(query_vars)
        expected_names = procedure.parameters_by_name
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
            query_string = query_string.decode("utf-8")

        if not query_string:
            return query_vars

        try:
            items = _parse_qs(query_string, strict_parsing=True)
        except ValueError:
            raise RequestError("Failed to parse query string")

        query_vars.update(items)

        return query_vars

    def _get_parameter_value(self, param):
        return self._parameter_values_by_parameter[param]

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

        @type content: str
        @param content: The response content

        @type content_type: str
        @param content_type: The response content MIME type

        @rtype: iterable<str>
        @return: The response content
        """

        return self._respond("200 OK", content, content_type)

    def respond_redirect(self, location):
        """
        Send 303 See Other

        @type location: str
        @param location: The target URI

        @rtype: iterable<str>
        @return: The response content
        """

        self.add_response_header("Location", str(location))
        return self._respond("303 See Other")

    def respond_not_modified(self):
        """
        Send 304 Not Modified

        @rtype: iterable<str>
        @return: The response content
        """

        return self._respond("304 Not Modified")

    def respond_not_found(self):
        """
        Send 404 Not Found

        @rtype: iterable<str>
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

        self.status = "500 Internal Server Error"

    def respond(self, request):
        content = self.render(request)
        content_type = "text/plain; charset=utf-8"

        content = content.encode("utf-8")
        
        return request._respond(self.status, content, content_type)

    def render(self, request):
        out = list()
        out.append("Error!")
        out.append("")
        out.append(self.render_summary(request))
        out.append("")
        out.append(self.render_details(request))
        return "\n".join(out)

    def render_details(self, request):
        out = list()
        out.append(self.render_traceback())
        out.append(self.render_request_details(request))
        out.append(self.render_application_details(request))
        return "\n".join(out)

    def render_traceback(self):
        if sys.exc_info()[1] is None:
            return ""

        content = _traceback.format_exc()
        return self.render_detail_section("Traceback", content)

    def render_request_details(self, request):
        out = list()

        content = fmt_dict(request._env)
        section = self.render_detail_section("WSGI environment", content)
        out.append(section)

        content = fmt_dict(get_app_request_info(request))
        section = self.render_detail_section("Request", content)
        out.append(section)

        return "".join(out)

    def render_application_details(self, request):
        out = list()

        content = fmt_dict(get_system_info())
        section = self.render_detail_section("System", content)
        out.append(section)

        return "".join(out)

    def render_detail_section(self, title, content):
        out = list()
        out.append(title)
        out.append("")

        if content is None:
            out.append("")
        else:
            out.append(content)

        return "\n".join(out)

    def render_summary(self, request):
        out = list()
        out.append(self.message)
        out.append("")
        out.append("Request errors")
        out.append("")
        
        for error in self.request.errors:
            out.append(" - {}".format(error.message))

        return "\n".join(out)

    def render_details(self, request):
        out = list()
        out.append(self.render_traceback())
        out.append(self.render_request_details())
        out.append(self.render_application_details(request))
        return "\n".join(out)

    def render_request_details(self):
        out = list()

        content = fmt_dict(get_request_info(self.request))
        section = self.render_detail_section("Request", content)
        out.append(section)
        out.append("")

        content = fmt_dict(get_session_info(self.request))
        section = self.render_detail_section("Session", content)
        out.append(section)        
        out.append("")

        return "\n".join(out)

class RequestErrorMessage:
    """
    @type request: L{Request}
    @ivar request: The request for which the error exists

    @type message: str
    @ivar message: The error message

    @undocumented: __init__, __repr__
    """

    def __init__(self, request, message):
        assert isinstance(request, Request)

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
        out.append("Yikes! An unexpected error:")
        out.append("")
        out.append(self.message)
        return "\n".join(out)

class _NotFoundError(RequestError):
    def __init__(self, request):
        super().__init__(request)

        self.title = "Not found!"
        self.status = "404 Not Found"

    def render_summary(self, request):
        path = "/".join(self.request.path)
        return "Nothing exists for path '{}'".format(path)

from .parameter import SecretParameter
