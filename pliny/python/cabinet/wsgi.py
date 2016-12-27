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

from application import *

from cherrypy.wsgiserver import CherryPyWSGIServer
from cherrypy.wsgiserver.ssl_builtin import BuiltinSSLAdapter

_log = logger("cabinet.wsgi")

class _WsgiServerThread(ApplicationThread):
    def __init__(self, app):
        super(_WsgiServerThread, self).__init__(app, "wsgi")

        self.run_again_on_error = False

        addr = self.app.host, self.app.port
        self.wsgi_server = CherryPyWSGIServer(addr, self.app._receive_request)

        ssl_adapter = BuiltinSSLAdapter(self.app.ssl_cert, self.app.ssl_key)
        self.wsgi_server.ssl_adapter = ssl_adapter

    def do_run(self):
        # CherryPy's .start is really a blocking .run
        self.wsgi_server.start()

    def stop(self):
        super(_WsgiServerThread, self).stop()
        self.wsgi_server.stop()
