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
Classes for defining L{Frames<Frame>}, including L{PageFrame}

@undocumented: __package__
"""

from application import *

_log = logger("cabinet.frame")

_http_date = "%a, %d %b %Y %H:%M:%S %Z"
_http_date_gmt = "%a, %d %b %Y %H:%M:%S GMT"

_content_types_by_extension = {
    ".css": "text/css",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".html": "application/xhtml+xml; charset=utf-8",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".js": "application/javascript",
    ".woff": "application/font-woff",
}

class Frame(object):
    """
    Control request processing for classes of request

    Frame instances are children of an L{Application}.

    @type app: L{Application}
    @ivar app: The parent application

    @type name: basestring
    @ivar name: The frame name

    @group Setup: __init__, init, delete
    @group Request processing: receive

    @undocumented: __repr__
    """

    def __init__(self, app, name):
        """
        Create a frame
        """

        self._app = app
        self._name = name

        assert self.app._initialized is False
        assert self.name not in self.app.frames_by_name

        self.app.frames.append(self)
        self.app.frames_by_name[self.name] = self

    @property
    def app(self):
        return self._app

    @property
    def name(self):
        return self._name

    def delete(self):
        """
        Delete the frame
        """

        self.app.frames.remove(self)
        del self.app.frames_by_name[self.name]

    def init(self):
        """
        Initialize the frame
        """

        _log.debug("Initializing %s", self)

    def receive(self, request):
        """
        Process one incoming request

        @type request: L{ApplicationRequest}
        @param request: The incoming request

        @rtype: iterable<basestring>
        @return: Response content

        @raise ApplicationRequestError: For expected errors

        @see: L{Application.receive}
        """

        raise NotImplementedError()

    def __repr__(self):
        args = self.__class__.__name__, self.name
        return "%s(%s)" % args

class PageFrame(Frame):
    """
    Process requests for L{Pages<Page>}

    PageFrame instances are children of an L{Application}.  Page frames
    hold L{Pages<Page>}.

    The page frame holds pages and dispatches requests to pages using
    the request path.

    @type pages: list<L{Page}>
    @ivar pages: A list of pages belonging to this frame in creation order

    @type pages_by_name: dict<basetring, L{Page}>
    @ivar pages_by_name: A dictionary of pages by page name

    @type default_page: L{Page}
    @ivar default_page: The page used if the page name is the empty string

    @group Page attributes: get_title, get_href
    @group Request processing: process
    """

    def __init__(self, app, name):
        super(PageFrame, self).__init__(app, name)

        self.pages = list()
        self.pages_by_name = dict()

        self.default_page = None

    def init(self):
        super(PageFrame, self).init()

        for page in self.pages:
            page.init()

        if self.default_page is not None:
            self.pages_by_name[""] = self.default_page

    def receive(self, request):
        try:
            page_name = request.path[1]
        except IndexError:
            page_name = ""

        try:
            page = self.pages_by_name[page_name]
        except KeyError:
            return request.send_not_found()

        return page.receive(request)

    def get_title(self, session):
        """
        The frame's pretty name

        By default this calls L{Page.get_title} on L{default_page} if set.

        @rtype: basestring
        @return: The frame title
        """

        if self.default_page is not None:
            return self.default_page.get_title(session)

    def get_href(self, session):
        """
        The frame URI

        By default this returns L{Application.get_href} + L{name}.

        @rtype: basestring
        @return: The frame href
        """

        args = self.app.get_href(session), self.name
        return "%s%s" % args

    def process(self, session):
        """
        Processing logic invoked after a L{Page} is resolved and before
        it is rendered

        @see: L{Page.receive}

        @rtype: basestring
        @return: A redirect URI or None
        """

        return None

class FileFrame(Frame):
    """
    Process requests for files

    @group Request processing: get_last_requested
    """

    def __init__(self, app, name):
        super(FileFrame, self).__init__(app, name)

        self.files_dir = os.path.join(self.app.home, "files")
        self.files_by_path = dict()

        self.last_modified = None

    def init(self):
        super(FileFrame, self).init()

        for root, dirs, files in os.walk(self.files_dir):
            for name in files:
                path = os.path.join(root, name)

                with open(path, "r") as file:
                    content = file.read()

                path = path[len(self.files_dir) + 1:]

                self.files_by_path[path] = content

        self.last_modified = datetime.now()
        self.last_modified = self.last_modified.replace(microsecond=0)

    def get_last_requested(self, request):
        """
        @rtype: datetime
        @return: The time the file was last requested
        """

        try:
            ims = request._env["HTTP_IF_MODIFIED_SINCE"]
        except KeyError:
            return

        try:
            return datetime(*time.strptime(str(ims), _http_date)[0:6])
        except AttributeError:
            return

    def receive(self, request):
        assert self.last_modified is not None

        lm = self.last_modified.strftime(_http_date_gmt)

        request.add_response_header("Last-Modified", lm)
        request.add_response_header("Cache-Control", "public, max-age=300")

        last_requested = self.get_last_requested(request)

        if last_requested is not None and last_requested >= self.last_modified:
            return request.send_not_modified()

        try:
            file_path = "/".join(request.path[1:])
        except IndexError:
            return request.send_not_found()

        try:
            content = self.files_by_path[file_path]
        except KeyError:
            return request.send_not_found()

        ext = os.path.splitext(file_path)[1]

        try:
            content_type = _content_types_by_extension[ext]
        except KeyError:
            raise ApplicationRequestError("Unknown content type")

        return request.respond("200 OK", content, content_type)
