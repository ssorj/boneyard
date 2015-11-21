# Copyright 2011 Red Hat, Inc.
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

from M2Crypto import httpslib, SSL
from exceptions import SSLVerificationError

# wrap the creation of a SSL.Context, etc in a class
class VerifiedHTTPSConnection(httpslib.HTTPSConnection):

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 root_cert=None, strict=None, timeout=None,
                 server_verify=True, 
                 domain_verify=True):
        """
        All params except those noted below are passed through to 
        the M2Crypto.httpslib.HTTPSConnection constructor.  Check docs on that
        class information.  Note, root_cert is passed in the SSL.Context if
        server_verify is True by means of SSL.Context.load_verify_locations.

        @param server_verify: does server certificate verification if True
        @param domain_verify: checks server certificate 'commonName' against host if True
        @param timeout: timeout value is set on the socket after connection using
                        socket.settimeout() if timeout is not None.
        """
        self.server_verify = server_verify
        self.domain_verify = domain_verify
        self._my_timeout = timeout

        ctx = SSL.Context()
        ctx.load_cert(cert_file, key_file)
        # Leaving the ctx verify mode set to 0 does not seem
        # to turn off all the server certificate checks, not
        # sure why.  Something in M2Crypto.  The hostname check
        # is still applied and raises an exception, so we catch
        # it as we do with domain_verify
        if server_verify:
            ctx.load_verify_locations(root_cert)
            mode = SSL.verify_peer | SSL.verify_fail_if_no_peer_cert
            ctx.set_verify(mode, depth=9)
        httpslib.HTTPSConnection.__init__(self, host, port, strict, 
                                          key_file=key_file, cert_file=cert_file,
                                          ssl_context=ctx)
    def connect(self):
        try:
            # Best we can do with the timeout parameter is
            # set it on the socket after the connection is
            # created.  There is no hook in M2Crypto to set
            # this prior to the connection.
            httpslib.HTTPSConnection.connect(self)
            if self._my_timeout is not None:
                self.sock.settimeout(self._my_timeout)
        except SSL.Checker.WrongHost, e:
            # Allow the host name check to fail if domain_verify is off.
            # This is mostly for testing with self-signed certificates 
            # and to provide the same interface as verifiedhttps.py
            # In order to squash the report of the mismatched hostnames,
            # we replace the message -- could be considered as a leak of
            # domain and certificate information I suppose.
            if self.server_verify and self.domain_verify:
                raise SSLVerificationError("Server certificate doesn't match domain;"\
                                           " untrusted connection")


