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

_log = logger("disco.debug")

# Query functions; these return dictionaries

def get_system_info():
    attrs = {
        "argv": sys.argv,
        "byteorder": sys.byteorder,
        "defaultencoding": sys.getdefaultencoding(),
        "filesystemencoding": sys.getfilesystemencoding(),
        "platform": sys.platform,
        "prefix": sys.prefix,
        "exec_prefix": sys.exec_prefix,
        "version": sys.version,
        "api_version": sys.api_version,
        }

    return attrs

def get_page_info(page):
    attrs = {
        "app": page.app,
        "frame": page.frame,
        "page": page,
        }

    return attrs

def get_parameters(request):
    return request._parameter_values_by_parameter

def get_request_info(request):
    attrs = {
        "attributes": request.attributes,
        "method": request.method,
        "path": request.path,
        "response_headers": request._response_headers,
        "session": request.session,
        }

    return attrs

def get_session_info(request):
    attrs = {
        "account": request.session.account,
        "attributes": request.attributes,
        "created": request.session.created,
        "result_message": request.session.result_message,
        "touched": request.session.touched,
    }

    return attrs

# Benchmarking

from urllib.parse import urlparse as _urlparse
from xml.etree.ElementTree import fromstring as _fromstring

class _BenchmarkHarness:
    def __init__(self, app):
        self.app = app
        self.continue_on_error = False

    def visit_uri(self, uri, depth):
        parsed_uri = _urlparse(uri)

        env = {
            "REQUEST_METHOD": "GET",
            "REQUEST_URI": uri,
            "PATH_INFO": parsed_uri.path,
            "QUERY_STRING": parsed_uri.query,
            }

        response_result = [None, None]

        def response(_status, _headers):
            response_result[0] = _status
            response_result[1] = dict(_headers)

        content = self.app._receive_request(env, response)
        content = "".join(content)

        status, headers = response_result

        if status.startswith("303"):
            return self.visit_uri(headers["Location"], depth + 1)

        return status, headers, content

    def get_content_uris(self, content):
        try:
            elem = _fromstring(content)
        except:
            print("Error in content:")
            print(content)
            raise

        uris = set()

        for anchor in elem.getiterator("{http://www.w3.org/1999/xhtml}a"):
            try:
                uri = anchor.attrib["href"]
            except KeyError:
                continue

            uri = re.sub(r"exit=.+?(&|;|$)", "", uri)

            uris.add(uri)

        return uris

    def run(self):
        unvisited_uris = deque()
        visited_uris = set()
        times = list()

        uri = "/"

        while True:
            visited_uris.add(uri)

            start = time.time()
            status, headers, content = self.visit_uri(uri, 0)
            stop = time.time()

            if headers["Content-Type"].startswith("application/xhtml+xml"):
                uris = self.get_content_uris(content)
                unvisited_uris.extend(uris.difference(visited_uris))

            elapsed_time = (stop - start) * 1000
            times.append(elapsed_time)

            args = len(times), elapsed_time, len(content), status, uri
            print("%6i [%.2f millis, %i bytes, %s] %s" % args)

            if not unvisited_uris:
                break

            uri = unvisited_uris.popleft()

        args = sum(times) / len(times), min(times), max(times)
        print("Time: avg %.2f millis, min %.2f, max %.2f" % args)
