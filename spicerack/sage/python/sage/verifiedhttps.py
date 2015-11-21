# Copyright 2011 Joseph Turner
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

# Copyright 2011 Red Hat, Inc.
#
# Modifications: addition of __init__ routine and 
#                member variables timeout, root_cert, server_verify,
#                and domain_verify for per instance control


import httplib
import socket
import ssl
from exceptions import SSLVerificationError

# Note: much thanks to Joseph Turner for showing the world
# how to extend httplib using the ssl module to implement
# server certificate validation.
# https://github.com/josephturnerjr/urllib2.VerifiedHTTPS

# subclass of HTTPSConnection to do cert verification and domain verification
class VerifiedHTTPSConnection(httplib.HTTPSConnection):

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 root_cert=None, strict=None, timeout=None,
                 server_verify=True, domain_verify=True):
        """
        All params except those noted below are passed through to 
        the httplib.HTTPSConnection constructor.  Check docs on that
        class information.

        @param root_cert: full path to root certificates file
        @param server_verify: does server certificate verification if True
        @param domain_verify: checks server certificate 'commonName' against host if True
        """
        httplib.HTTPSConnection.__init__(self, host, port, key_file, cert_file,
                                         strict)
        # Handle difference between Python 2.4 and 2.6.  Timeout was added
        # in 2.6, and if not specified will be the global default timeout.
        # In this routine allow None to indicate default, otherwise set the 
        # value since we can't set it in the constructor.  If it's missing
        # we will create it here.
        if timeout is not None:
            self.timeout = timeout
        
        self.root_cert = root_cert
        self.server_verify = server_verify
        self.domain_verify = domain_verify

    def connect(self):
        # overrides the version in httplib so that we do certificate verification
        try:
            # this is a convenience function added in python 2.6
            sock = socket.create_connection((self.host, self.port), self.timeout)
        except AttributeError:
            # There is no timeout attribute in earlier versions of this object.
            # The only option available is to set a global default timeout for
            # all socket objects.
            if hasattr(self, "timeout"):
                socket.setdefaulttimeout(self.timeout)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))

        # This code is not available for older versions of python and seems to
        # have no effect on establishing a verified https connection.
        #if self._tunnel_host:
        #    self.sock = sock
        #    self._tunnel()

        if self.server_verify:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, 
                                        cert_reqs=ssl.CERT_REQUIRED, 
                                        ca_certs=self.root_cert)
            if self.domain_verify:
                cert_subject = self.sock.getpeercert()['subject']
                cert_dict = {}
                for c in cert_subject:
                    cert_dict.update(c)
                cert_host = cert_dict['commonName']
                if self.host != cert_host:
                    raise SSLVerificationError("Server certificate doesn't match domain;"\
                                               " untrusted connection")
        else:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file) 


