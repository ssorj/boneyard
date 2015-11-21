from https import HTTPSClientAuthHandler, HTTPSClientCertTransport

# If verifiedhttps dependencies can be satisfied, 
# this import will succeed and the following two classes will
# be available to provide server certificate validation.
try:
    # Try a solution that uses the Python ssl module first
    from sage.verifiedhttps import VerifiedHTTPSConnection
    technology = "Python ssl"
except:
    # Didn't work, try a solution based on m2crypto
    from sage.verifiedhttps_m2crypto import VerifiedHTTPSConnection
    technology = "M2Crypto"

class HTTPSFullAuthHandler(HTTPSClientAuthHandler):
    """
    Add server certificate validation to HTTPSClientAuthHandler
    via a different connection type (VerifiedHTTPSConnection).
    """
    def __init__(self, my_key, my_cert, root_cert, domain_verify):
        """
        @param my_key: full path for the client's private key file
        @param my_cert: full path for the client's PEM certificate file
        @param root_cert: full path for root certificates file used to
        verify server certificates on connection
        @param domain_verify: check server host against the 'commonName'
        field in the server certificate
        """
        self.root_cert = root_cert
        self.domain_verify = domain_verify
        HTTPSClientAuthHandler.__init__(self, my_key, my_cert)

    def _get_connection(self, host, timeout=300):
        """
        @return: A connection object derived from httplib types with
        with client and server certificate validation support
        @rtype: VerifiedHTTPSConnection
        """
        return VerifiedHTTPSConnection(host,
                                       key_file=self.key,
                                       cert_file=self.cert,
                                       root_cert=self.root_cert,
                                       domain_verify=self.domain_verify)

class HTTPSFullCertTransport(HTTPSClientCertTransport):
    """
    Add server certificate validation to HTTPSClientCertTransport
    via a different handler type (HTTPSFullAuthHandler)
    """
    def __init__(self, key, cert, root_cert, domain_verify=True, 
                 *args, **kwargs):
        """
        @param key: full path for the client's private key file
        @param cert: full path for the client's PEM certificate file
        @param root_cert: full path for root certificates file used to
        verify server certificates on connection
        @param domain_verify: check server host against the 'commonName'
        field in the server certificate            
        """
        self.root_cert = root_cert
        self.domain_verify = domain_verify
        HTTPSClientCertTransport.__init__(self, key, cert, *args, **kwargs)

    def _get_auth_handler(self):
        return HTTPSFullAuthHandler(self.key, self.cert, self.root_cert,
                                    self.domain_verify)
