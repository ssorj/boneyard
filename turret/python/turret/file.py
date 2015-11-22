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

_log = logger("turret.file")

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
    ".txt": "text/plain; charset=utf-8",
    ".woff": "application/font-woff",
}

class File:
    """
    A static file
    """
    
    def __init__(self, app, path):
        """
        Create a file
        """
        
        self._app = app
        self._path = path

        self._content = None
        self._content_type = None
        self._last_modified = None

        assert not self.app._initialized
        assert self.path not in self.app.files_by_path

        self.app.files.append(self)
        self.app.files_by_path[self.path] = self

    def __repr__(self):
        return fmt_repr(self, self.path)

    @property
    def app(self):
        return self._app

    @property
    def path(self):
        return self._path

    @property
    def content(self):
        return self._content

    @property
    def content_type(self):
        return self._content_type

    @property
    def last_modified(self):
        return self._last_modified

    def init(self):
        """
        Initialize the file
        """

        _log.debug("Initializing %s", self)

        path = os.path.join(self.app.files_dir, self.path)
        
        with open(path, "rb") as file:
            self._content = file.read()

        ext = os.path.splitext(self.path)[1]

        try:
            self._content_type = _content_types_by_extension[ext]
        except KeyError:
            raise ApplicationError("Unknown content type")
        
        self._last_modified = datetime.now()
        self._last_modified = self._last_modified.replace(microsecond=0)
            
    def receive_request(self, request):
        _log.debug("Receiving request for %s", self)
        
        """
        Process a file request and respond with the file content
        """

        assert self.last_modified is not None

        last_modified = self.last_modified.strftime(_http_date_gmt)

        request.add_response_header("Last-Modified", last_modified)
        request.add_response_header("Cache-Control", "public, max-age=300")

        last_requested = self.get_last_requested(request)

        if last_requested is not None and last_requested >= self.last_modified:
            return request.respond_not_modified()

        return request.respond_ok(self.content, self.content_type)

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

from .parameter import *
