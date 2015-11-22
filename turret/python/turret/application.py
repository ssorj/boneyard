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

@sort: Application, ApplicationThread, ApplicationError
"""

from .common import *

import threading as _threading

_log = logger("turret.application")

class Application:
    """
    The root of the Turret object hierarchy

    The application holds Procedures.

    The application object is responsible for

     - Storing application configuration
     - Processing HTTP requests
     - Reporting errors encountered while processing requests

    @type frames: list<L{Frame}>
    @ivar frames: A list of application frames in creation order

    @type frames_by_name: dict<basestring, L{Frame}>
    @ivar frames_by_name: A dictionary of application frames by frame name

    @type default_frame: L{Frame}
    @ivar default_frame: The frame used if the frame name is the empty
    string

    @group Setup: __init__, init, start, stop
    @group Page attributes: get_*
    @group Request processing: receive_request, process

    @undocumented: __repr__, __class__
    """

    def __init__(self, home_dir, files_dir):
        """
        Create an application
        """

        self._home_dir = home_dir
        self._files_dir = files_dir
        
        self.procedures = list()
        self.procedures_by_name = dict()

        self.files = list()
        self.files_by_path = dict()

        self._session_expire_thread = _SessionExpireThread(self)
        self._sessions_by_id = dict()

        self._initialized = False
        self._started = False
        self._stopped = False

    def __repr__(self):
        return fmt_repr(self)

    @property
    def home_dir(self):
        return self._home_dir
    
    @property
    def files_dir(self):
        return self._files_dir

    # perhaps load() with file and config loading
    
    def init(self):
        """
        Initialize the application

        This triggers initialization of the Turret object hierarchy.

        @see: L{Procedure.init}, L{Parameter.init}, L{File.init}
        """

        _log.info("Initializing %s", self)

        assert not self._initialized
        assert not self._started
        assert not self._stopped

        for proc in self.procedures:
            proc.init()

        for root, dirs, files in os.walk(self.files_dir):
            for name in files:
                path = os.path.join(root, name)
                path = path[len(self.files_dir) + 1:]

                file = File(self, path)

        for file in self.files:
            file.init()

        self._initialized = True

    def start(self):
        """
        Start the application

        This starts the application threads.  It must be called only once,
        after L{init}.
        """

        _log.info("Starting %s", self)

        assert self._initialized
        assert not self._started
        assert not self._stopped

        self._session_expire_thread.start()

        self._started = True

    def stop(self):
        """
        Stop the application

        This stops the application threads.  It must be called only once,
        after L{start}.
        """

        _log.info("Stopping %s", self)

        assert self._initialized
        assert self._started
        assert not self._stopped

        self._stopped = True

    def application(self, env, start_response):
        request = Request(self, env, start_response)

        try:
            request._load()
        except:
            _log.exception("Unexpected error")

            return request._respond_unexpected_error()

        _log.info("Receiving %s", request)
        
        csp = "default-src: 'self'"
        sts = "max-age=31536000"

        request.add_response_header("Content-Security-Policy", csp)
        request.add_response_header("Strict-Transport-Security", sts)

        try:
            return self.receive_request(request)
        except RequestError:
            _log.exception("Application error")

            try:
                return request._respond_application_error()
            except:
                _log.exception("Unexpected error")

                return request._respond_unexpected_error()
        except:
            _log.exception("Unexpected error")
            return request._respond_unexpected_error()

    def receive_request(self, request):
        """
        Process one incoming request

        @type request: L{Request}
        @param request: The incoming request

        @rtype: iterable<bytes>
        @return: Response content

        @raise RequestError: For expected errors
        """

        try:
            proc_prefix = request.path[0]
        except IndexError:
            proc_prefix = None

        if proc_prefix == "_procedures":
            return self.receive_request_for_procedure(request)
        
        return self.receive_request_for_file(request)

    def receive_request_for_procedure(self, request):
        try:
            proc_name = request.path[1]
        except IndexError:
            return request.respond_not_found()
            
        try:
            proc = self.procedures_by_name[proc_name]
        except KeyError:
            return request.respond_not_found()

        request._load_parameter_values(proc)
        
        return proc.receive_request(request)

    def receive_request_for_file(self, request):
        try:
            file_path = "/".join(request.path)
        except IndexError:
            return request.respond_not_found()

        try:
            file = self.files_by_path[file_path]
        except KeyError:
            return request.respond_not_found()

        return file.receive_request(request)

    # XXX
    def process(self, request):
        """
        Processing logic invoked after a L{Page} is resolved and before
        it is rendered

        @see: L{Page.receive_request}

        @rtype: basestring
        @return: A redirect URI or None
        """

        return None

class ApplicationThread(_threading.Thread):
    """
    For L{Application} threads

    By default, ApplicationThreads are daemon threads.

    @type app: L{Application}
    @ivar app: The containing application

    @type name: str
    @ivar name: The thread's name

    @type run_again_on_error: boolean
    @ivar run_again_on_error: Repeat execution of L{do_run} after
    unexpected errors (default True)

    @undocumented: __repr__
    """

    def __init__(self, app, name):
        super().__init__()

        self.app = app
        self.name = name
        self.run_again_on_error = True
        self.daemon = True

    def init(self):
        _log.debug("Initializing %s", self)

    def start(self):
        _log.debug("Starting %s", self)

        super().start()

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
        return fmt_repr(self, self.name)

class ApplicationError(Exception):
    """
    The base L{Application} error type

    @undocumented: __init__, __repr__
    """

    def __init__(self, message):
        super().__init__()

        self.message = message

    def __repr__(self):
        return fmt_repr(self, self.message)

from .session import Session, _SessionExpireThread
from .debug import *
from .request import *
from .file import *
