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

_log = logger("turret.procedure")

class Procedure:
    """
    A named procedure
    """
    
    def __init__(self, app, name):
        """
        Create a procedure
        """
        
        self._app = app
        self._name = name

        self.parameters = list()
        self.parameters_by_name = dict()

        assert not self.app._initialized
        assert self.name not in self.app.procedures_by_name

        self.app.procedures.append(self)
        self.app.procedures_by_name[self.name] = self

    def __repr__(self):
        return fmt_repr(self, self.name)

    @property
    def app(self):
        return self._app

    @property
    def name(self):
        return self._name

    def init(self):
        """
        Initialize the procedure
        """
        
        _log.debug("Initializing %s", self)

        for param in self.parameters:
            param.init()

    def get_content_type(self, request):
        """
        Get the value for the HTTP Content-Type header
        """
        
        return "application/json; charset=utf-8"

    def receive_request(self, request):
        """
        Process a procedure call and respond with the result
        """
        
        redirect = self.app.process(request)

        if redirect is not None:
            return request.respond_redirect(redirect)
        
        redirect = self.process(request)

        if redirect is not None:
            return request.respond_redirect(redirect)
        
        content = self.render(request)
        content_type = self.get_content_type(request)

        content = content.encode("utf-8")

        return request.respond_ok(content, content_type)

    def process(self, request):
        _log.debug("Processing %s", self)

        self.load_parameters(request)

        # XXX request.check_errors()

        self.validate_parameters(request)

        # XXX request.check_errors()

        redirect = self.do_process(request)

        # XXX request.check_errors()

        return redirect

    def do_process(self, request):
        """
        A standard extension point for processing
        """
        
        return None
    
    def load_parameters(self, request):
        """
        Load parameter values from the request
        """

        for param in self.parameters:
            param.load(request)

    def validate_parameters(self, request):
        """
        Check for invalid parameter values and accumulate any errors
        """

        for param in self.parameters:
            param.validate(request)

    def render(self, request):
        pass
        
from .parameter import *
