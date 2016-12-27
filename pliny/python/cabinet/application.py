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
Classes for defining L{Applications<Application>}

@sort: Application, ApplicationRequest, ApplicationRequestError,
ApplicationThread
"""

from common import *

import threading as _threading

_log = logger("cabinet.application")
_strings = StringCatalog(__file__)

class Application(object):
    """
    The root of the Cabinet object hierarchy

    The application holds L{Frames<Frame>}, which in trun hold
    L{Pages<Page>}.

    The application object is responsible for

     - Storing application configuration
     - Processing HTTP requests
     - Reporting errors encountered while processing requests

    @type home: basestring
    @ivar home: The path to the application home directory

    @type host: basestring
    @ivar host: The network interface on which to serve requests

    @type port: basestring
    @ivar port: The network port on which to serve requests

    @type ssl_cert: basestring
    @ivar ssl_cert: The path to a PEM-formatted SSL certificate

    @type ssl_key: basestring
    @ivar ssl_key: The path to a PEM-formatted SSL key

    @type frames: list<L{Frame}>
    @ivar frames: A list of application frames in creation order

    @type frames_by_name: dict<basestring, L{Frame}>
    @ivar frames_by_name: A dictionary of application frames by frame name

    @type default_frame: L{Frame}
    @ivar default_frame: The frame used if the frame name is the empty
    string

    @group Setup: __init__, init, start, stop
    @group Page attributes: get_*
    @group Request processing: receive, process

    @undocumented: __repr__, __class__
    """

    def __init__(self, home, host, port, ssl_cert, ssl_key):
        """
        Create an application
        """

        self._home = home

        self._host = host
        self._port = port

        self._ssl_cert = ssl_cert
        self._ssl_key = ssl_key

        self.frames = list()
        self.frames_by_name = dict()

        self.default_frame = None

        self._client_session_expire_thread = _ClientSessionExpireThread(self)
        self._client_sessions_by_id = dict()

        self._wsgi_server_thread = _WsgiServerThread(self)

        self._not_found_error = _NotFoundError()

        self._initialized = False
        self._started = False
        self._stopped = False

    @property
    def home(self):
        return self._home

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def ssl_cert(self):
        return self._ssl_cert

    @property
    def ssl_key(self):
        return self._ssl_key

    def init(self):
        """
        Initialize the application

        This triggers initialization of the Cabinet object hierarchy.

        @see: L{Frame.init}, L{Page.init}, L{Parameter.init},
        L{RenderObject.init}
        """

        _log.info("Initializing %s", self)

        assert self._initialized is False
        assert self._started is False
        assert self._stopped is False

        for frame in self.frames:
            frame.init()

        if self.default_frame is not None:
            self.frames_by_name[""] = self.default_frame

        self._initialized = True

    def start(self):
        """
        Start the application

        This starts the application threads.  It must be called only once,
        after L{init}.
        """

        _log.info("Starting %s", self)

        assert self._initialized is True
        assert self._started is False
        assert self._stopped is False

        self._client_session_expire_thread.start()
        self._wsgi_server_thread.start()

        self._started = True

    def stop(self):
        """
        Stop the application

        This stops the application threads.  It must be called only once,
        after L{start}.
        """

        _log.info("Stopping %s", self)

        assert self._initialized is True
        assert self._started is True
        assert self._stopped is False

        self._wsgi_server_thread.stop()

        self._stopped = True

    def _receive_request(self, env, start_response):
        request = ApplicationRequest(self, env, start_response)

        _log.info("Receiving %s", request)
        
        csp = "default-src: 'self'"
        sts = "max-age=31536000"

        request.add_response_header("Content-Security-Policy", csp)
        request.add_response_header("Strict-Transport-Security", sts)

        try:
            return self.receive(request)
        except ApplicationRequestError:
            _log.exception("Application error")
            try:
                return request._send_application_error()
            except:
                _log.exception("Unexpected error")
                return request._send_unexpected_error()
        except:
            _log.exception("Unexpected error")
            return request._send_unexpected_error()

    def receive(self, request):
        """
        Process one incoming request

        It looks up a frame using the path and calls its L{Frame.receive}
        method.

        @type request: L{ApplicationRequest}
        @param request: The incoming request

        @rtype: iterable<basestring>
        @return: Response content

        @raise ApplicationRequestError: For expected errors
        """

        try:
            frame_name = request.path[0]
        except IndexError:
            frame_name = ""

        try:
            frame = self.frames_by_name[frame_name]
        except KeyError:
            return request.send_not_found()

        return frame.receive(request)

    def get_title(self, session):
        """
        The application's pretty name

        By default this calls L{PageFrame.get_title} on L{default_frame}
        if set.

        @rtype: basestring
        @return: The application title
        """

        if self.default_frame is not None:
            return self.default_frame.get_title(session)

    def get_href(self, session):
        """
        The application URI

        By default this returns "/".  If overriden, the value returned must
        have a trailing slash.

        @rtype: basestring
        @return: The application URI
        """

        return "/"

    def process(self, session):
        """
        Processing logic invoked after a L{Page} is resolved and before
        it is rendered

        @see: L{Page.receive}

        @rtype: basestring
        @return: A redirect URI or None
        """

        return None

    def __repr__(self):
        args = self.__class__.__name__, self.host, self.port, self.home
        return "%s(%s,%s,%s)" % args

class ApplicationRequest(object):
    """
    The state of one L{Application} request and methods for sending a
    response

     - It is created once for each call to L{Application.receive}
     - It accumulates output headers for the response

    @type path: iterable<basestring>
    @ivar path: Preparsed elements of the requested path (PATH_INFO)

    @type method: basestring
    @ivar method: The HTTP request method (GET, POST, etc.)

    @type uri: basestring
    @ivar uri: The URI as requested by the HTTP client

    @type attributes: dict
    @ivar attributes: Application-defined name-value attributes

    @group Response generation: add_response_header, respond, send_*

    @undocumented: __init__, __repr__
    """

    def __init__(self, app, env, start_response):
        self._app = app
        self._env = env
        self._start_response = start_response
        self._response_headers = list()

        path = self._env["PATH_INFO"][1:].split("/")
        path = map(url_unescape, path)

        self.path = path
        self.method = self._env["REQUEST_METHOD"]
        self.uri = self._env["REQUEST_URI"]
        self.attributes = dict()

    def add_response_header(self, name, value):
        """
        Add a header to the response

        @type name: basestring
        @param name: The header name

        @type value: basestring
        @param value: The header value
        """

        # wsgiserver seems to choke on unicode
        assert isinstance(value, str)

        self._response_headers.append((name, value))

    def respond(self, status, content=None, content_type=None):
        """
        Respond to this request

        It starts the WSGI server response and returns the content.

        @type status: basestring
        @param status: The HTTP status string ("200 OK", "404 Not Found", etc.)

        @type content: basestring
        @param content: The response content

        @type content_type: basestring
        @param content_type: The response content MIME type

        @rtype: iterable<basestring>
        @return: The response content
        """

        _log.info("Responding %s", status)

        client = self.attributes.get("cabinet.set-client-session")

        if client is not None:
            value = "session=%s; Path=/; Secure; HttpOnly" % client._id
            self.add_response_header("Set-Cookie", value)

        if content is None:
            self.add_response_header("Content-Length", "0")
            self._start_response(status, self._response_headers)
            return ("",)

        assert content_type is not None

        content_length = len(content)

        self.add_response_header("Content-Length", str(content_length))
        self.add_response_header("Content-Type", content_type)

        self._start_response(status, self._response_headers)

        return (content,)

    def send_redirect(self, location):
        """
        Send 303 See Other

        This internally calls L{respond}.

        @type location: basestring
        @param location: The target URI

        @rtype: iterable<basestring>
        """

        self.add_response_header("Location", str(location))
        return self.respond("303 See Other")

    def send_not_modified(self):
        """
        Send 304 Not Modified

        This internally calls L{respond}.

        @rtype: iterable<basestring>
        """

        return self.respond("304 Not Modified")

    def send_not_found(self):
        """
        Send 404 Not Found

        This internally calls L{respond}.

        @rtype: iterable<basestring>
        """

        return self._app._not_found_error.send_message(self)

    def _send_application_error(self):
        error = sys.exc_info()[1]
        return error.send_message(self)

    def _send_unexpected_error(self):
        exc = sys.exc_info()[1]
        error = _UnexpectedError(exc)
        return error.send_message(self)

    def __repr__(self):
        args = self.__class__.__name__, self.method, self.uri
        return "%s(%s,%s)" % args

class ApplicationError(Exception):
    """
    The base L{Application} error type

    @undocumented: __init__, __repr__
    """

    def __init__(self, message):
        super(ApplicationError, self).__init__()

        self.message = message

        self.template = _strings["error_message"]
        self.title = "Error!"
        self.status = "500 Internal Server Error"

    def send_message(self, request):
        content = self.render(request)
        content_type = "application/xhtml+xml; charset=utf-8"

        return request.respond(self.status, content, content_type)

    def render(self, request):
        args = {
            "navigation": html_link("Home", "/"),
            "title": xml_escape(self.title),
            "summary": self.render_summary(request),
            "details": self.render_details(request),
        }

        return self.template.format(**args)

    def render_summary(self, request):
        return xml_escape(self.message)

    def render_details(self, request):
        out = list()
        out.append(self.render_traceback())
        out.append(self.render_request_details(request))
        out.append(self.render_application_details(request))
        return "".join(out)

    def render_traceback(self):
        if sys.exc_info()[1] is None:
            return ""

        content = xml_escape(traceback.format_exc())
        return self.render_detail_section("Traceback", content)

    def render_request_details(self, request):
        out = list()

        content = _fmt_dict(request._env)
        section = self.render_detail_section("WSGI environment", content)
        out.append(section)

        content = _fmt_dict(get_request_info(request))
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

    def __repr__(self):
        args = self.__class__.__name__, self.message
        return "%s(%s)" % args

class ApplicationRequestError(ApplicationError):
    """
    For L{Application} errors

    ApplicationRequestErrors are trapped and reported during L{Application}
    request processing.

    @undocumented: __repr__
    """

class _UnexpectedError(ApplicationError):
    def __init__(self, exception):
        super(_UnexpectedError, self).__init__(str(exception))

        self.wrapped_exception = exception

    def render_summary(self, request):
        out = list()
        out.append(html_p("Yikes! An unexpected error:"))
        out.append(html_elem("pre", xml_escape(self.message)))
        return "".join(out)

class _NotFoundError(ApplicationError):
    def __init__(self):
        super(_NotFoundError, self).__init__(None)

        self.title = "Not found!"
        self.status = "404 Not Found"

    def render_summary(self, request):
        return "Nothing exists for path '%s'" % xml_escape(request.uri)

class ApplicationThread(_threading.Thread):
    """
    For L{Application} threads

    By default, ApplicationThreads are daemon threads.

    @type app: L{Application}
    @ivar app: The containing application

    @type name: basestring
    @ivar name: The thread's name

    @type run_again_on_error: boolean
    @ivar run_again_on_error: Repeat execution of L{do_run} after
    unexpected errors (default True)

    @undocumented: __repr__
    """

    def __init__(self, app, name):
        super(ApplicationThread, self).__init__()

        self.app = app
        self.name = name
        self.run_again_on_error = True
        self.daemon = True

    def init(self):
        _log.debug("Initializing %s", self)

    def start(self):
        _log.debug("Starting %s", self)

        super(ApplicationThread, self).start()

    def run(self):
        _log.debug("Running %s", self)

        while True:
            try:
                self.do_run()
            except KeyboardInterrupt:
                raise
            except:
                _log.exception("Unexpected error")

            if not self.run_again_on_error:
                break

            time.sleep(1)

    def do_run(self):
        """
        The default extension point, called from L{run}

        Any exceptions thrown by this method are caught and logged in L{run}.
        If L{run_again_on_error} is enabled, it is then called again.
        """

        raise NotImplementedError()

    def stop(self):
        """
        Stop the thread's activity
        """

        _log.debug("Stopping %s", self)

    def __repr__(self):
        args = self.__class__.__name__, self.name
        return "%s(%s)" % args

def _fmt_dict(coll):
    return xml_escape(fmt_dict(coll))

from client import ClientSession, _ClientSessionExpireThread
from debug import *
from wsgi import _WsgiServerThread
