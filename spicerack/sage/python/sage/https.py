# Copyright 2011 David Norton, Jr.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# http://davidnortonjr.com/

# Copyright 2011 Red Hat, Inc.
#
# Modifications: inclusion of doc strings, method and class name changes,
#                provide _get_auth_handler method which can be overloaded
#                in derived classes.

# uses Suds - https://fedorahosted.org/suds/
import urllib2 as u2
from suds.transport.http import HttpTransport
import httplib

class HTTPSClientAuthHandler(u2.HTTPSHandler):  
    def __init__(self, key, cert):
        """
        @param key: full path for the client's private key file
        @param cert: full path for the client's PEM certificate file
        """
        u2.HTTPSHandler.__init__(self)  
        self.key = key  
        self.cert = cert  

    def https_open(self, req):
        """
        Override https_open() in the HTTPSHandler class.

        The inherited method does not set private key and certificate values on
        the HTTPSConnection object.
        """
        # Rather than pass in a reference to a connection class, we pass in  
        # a reference to a function which, for all intents and purposes,  
        # will behave as a constructor 
        return self.do_open(self._get_connection, req) 

    def _get_connection(self, host, timeout=300):
        """
        @return: an HTTPSConnection object constructed with private key and 
        certificate values supplied.
        @rtype: HTTPSConnection
        """
        return httplib.HTTPSConnection(host, key_file=self.key, cert_file=self.cert)  

class HTTPSClientCertTransport(HttpTransport):
    def __init__(self, key, cert, *args, **kwargs):
        """
        @param key: full path for the client's private key file
        @param cert: full path for the client's PEM certificate file
        """
        HttpTransport.__init__(self, *args, **kwargs)
        self.key = key
        self.cert = cert
        self.urlopener = u2.build_opener(self._get_auth_handler())

    def _get_auth_handler(self):
        return HTTPSClientAuthHandler(self.key, self.cert)


