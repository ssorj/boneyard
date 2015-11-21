# XXX get rid of this

from wooly.server import WebServer

class CuminServer(WebServer):
    def __init__(self, app, host, port, server_cert="", server_key=""):

        # Elements of WebServer will look for the cert/key fields
        self.server_cert = server_cert
        self.server_key = server_key

        # If ssl is enabled successfully, this flag will be set
        # to true.
        self.ssl_enabled = False
        self.force_secure_cookies = app.force_secure_cookies

        super(CuminServer, self).__init__(app, host, port)

    def authorized(self, session):
        return True
