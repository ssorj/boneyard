import socket

from util import *
from wooly import *
from wsgiserver import CherryPyWSGIServer

log = logging.getLogger("wooly.server")

class WebServer(object):
    http_date = "%a, %d %b %Y %H:%M:%S %Z"
    http_date_gmt = "%a, %d %b %Y %H:%M:%S GMT"

    def __init__(self, app, host, port):
        self.log = log

        self.app = app

        self.host = host
        self.port = port

        self.ssl_enabled = False
        # XXX Gah, why is the word server in here?
        self.server_cert = None
        self.server_key = None

        self.dispatch_thread = WebServerDispatchThread(self)

        self.client_sessions_by_id = dict()
        self.client_session_expire_thread = ClientSessionExpireThread(self)

    def init(self):
        return # XXX urgh

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            for i in range(60):
                try:
                    s.bind((self.host, self.port))
                    return
                except socket.error:
                    log.warn("Address %s:%i is taken; retrying",
                             self.host, self.port)
                    time.sleep(5)
        finally:
            s.close()

        raise Exception("Failed to bind to %s:%i" % (self.host, self.port))

    def start(self):
        log.info("Starting %s", self)

        self.dispatch_thread.start()
        self.client_session_expire_thread.start()

    def stop(self):
        log.info("Stopping %s", self)

        self.dispatch_thread.stop()

    def get_page(self, env):
        name = env["PATH_INFO"][1:]

        return self.app.pages_by_name.get(name)

    def get_last_requested(self, env):
        try:
            ims = env["HTTP_IF_MODIFIED_SINCE"]
        except KeyError:
            return None
        
        try:
            then = datetime(*time.strptime(str(ims), self.http_date)[0:6])
        except AttributeError:
            return None

        return then

    def service_request(self, env, response):
        log.info("Request %s %s", env["REQUEST_METHOD"], env["REQUEST_URI"])

        page = self.get_page(env)

        if page:
            status, headers, content = self.service_page_request(page, env)
        else:
            status = "404 Not Found"
            headers = ()
            content = ""

        response(status, headers)

        log.info("Response %s", status)

        log.debug("Response headers:")

        for header in headers:
            log.debug("  %-24s  %s", *header)

        return (content,)

    # XXX consider moving this closer to Page or a WsgiPageAdapter
    def service_page_request(self, page, env):
        session = Session(page)

        self.adapt_request_to_session(env, session)

        #log.debug("Using %s, %s", page, session.client_session)

        status = None
        headers = list()
        content = ""

        last_modified = page.get_last_modified(session)
        last_requested = self.get_last_requested(env)

        if last_modified:
            last_modified = last_modified.replace(microsecond=0)

            value = last_modified.strftime(self.http_date_gmt)
            headers.append(("Last-Modified", value))

        if last_modified is None or last_requested is None \
                or last_modified > last_requested:
            try:
                content = page.service(session)
                status = "200 OK"
            except PageRedirect:
                status = "303 See Other"
                url = page.redirect.get(session)

                headers.append(("Location", url))
            except:
                content = page.service_error(session)
                status = "500 Internal Error"
        else:
            status = "304 Not Modified"

        if content:
            content_length = str(len(content))
            content_type = page.get_content_type(session)

            headers.append(("Content-Length", content_length))
            headers.append(("Content-Type", content_type))

            # additional headers take the form of an array of tuples
            # ie [("Content-description", "File Transfer")]
            content_extra_headers = page.get_extra_headers(session)
            for extra_header in content_extra_headers:
                headers.append(extra_header)

        cache = page.get_cache_control(session)

        if cache:
            headers.append(("Cache-Control", cache))

        secure_cookies = True # XXX self.ssl_enabled or self.force_secure_cookies
        for header in session.marshal_cookies(secure_cookies):
            headers.append(("Set-Cookie", header))

        # Make sure that we have no headers containing LF characters
        # which could be a result of a response splitting attempt.
        for header in headers:
            if "\n" in header[1]:
                log.error("Response header contains LF (#), %s:%s" % \
                         (header[0], header[1].replace("\n", "#"))) 
                raise Exception("Unexpected LF in response header")

        return status, headers, content

    def adapt_request_to_session(self, env, session):
        session.unmarshal_url_vars(env["QUERY_STRING"])

        if env["REQUEST_METHOD"] == "POST":
            content_type = env["CONTENT_TYPE"]

            if content_type == "application/x-www-form-urlencoded":
                length = int(env["CONTENT_LENGTH"])
                vars = env["wsgi.input"].read(length)
            else:
                raise Exception \
                    ("Content type '%s' is not supported" % content_type)

            if vars:
                session.unmarshal_url_vars(vars, "&")

        try:
            session.unmarshal_cookies(env["HTTP_COOKIE"])
        except KeyError:
            pass

        session.request_environment = env
        session.client_session = self.get_client_session(session)

    def get_client_session(self, session):
        try:
            csession_id = session.cookies_by_name["session"][1]
            csession = self.client_sessions_by_id[csession_id]
        except KeyError:
            csession = ClientSession()
            self.client_sessions_by_id[csession.id] = csession
            session.set_cookie("session", csession.id)

        csession.visited = datetime.now()
        return csession

    def reset_client_session_id(self, session, login):

        # Take the client session out of the dict.
        # We're going to insert a new one.  Running threads that
        # have a reference will continue to execute...
        try:
            del self.client_sessions_by_id[session.client_session.id]
        except KeyError:
            pass

        nclient = ClientSession()
        # we've already got copy.copy from wooly.util
        nclient.attributes = copy(session.client_session.attributes)
        nclient.attributes["login_session"] = login
        nclient.visited = datetime.now()
        self.client_sessions_by_id[nclient.id] = nclient
            
        # ...and reset the cookie for the broswer
        session.client_session = nclient
        session.set_cookie("session", session.client_session.id)

    def __repr__(self):
        return "%s(%s,%i)" % (self.__class__.__name__, self.host, self.port)

class WebServerDispatchThread(Thread):
    def __init__(self, server):
        super(WebServerDispatchThread, self).__init__()

        self.server = server
        self.name = self.__class__.__name__

        self.setDaemon(True)
        
        self.wsgi_server = CherryPyWSGIServer \
            ((self.server.host, self.server.port),
             self.server.service_request,
             request_queue_size=32,
             numthreads=32,
             max=32)
    
        if self.server.server_cert and self.server.server_key:
            ssl_adapter = None

            # Try the Python ssl module solution first
            try:
                from wsgiserver.ssl_builtin import BuiltinSSLAdapter
                ssl_adapter = BuiltinSSLAdapter(self.server.server_cert,
                                                self.server.server_key)
                log.info("Webserver: ssl enabled via the Python ssl module.")
            except:
                pass

            if ssl_adapter is None:
                try:
                    from wsgiserver.ssl_pyopenssl import pyOpenSSLAdapter
                    ssl_adapter = pyOpenSSLAdapter(self.server.server_cert,
                                                   self.server.server_key)
                    log.info("Webserver: ssl enabled via the pyOpenSSL module.")
                except:
                    pass

            if ssl_adapter is None:
                log.warn("Webserver: SSL was requested, but imports failed "
                         "for SSL implementations. Running with http only.")
            else:
                self.server.ssl_enabled = True
                self.wsgi_server.ssl_adapter = ssl_adapter

        self.wsgi_server.environ["wsgi.version"] = (1, 1)

    def run(self):
        try:
            from ssl import SSLError
        except:
            class SSLError(Exception):
                pass

        try:
            from OpenSSL import SSL
        except:
            class SSL(object):
                class Error(Exception):
                    pass

        try:
            self.wsgi_server.start()
        except (SSLError, SSL.Error), e:
            log.error("Web server is shutting down from an unhandled SSLError" \
                      " (problem with the key or certificate?): %s" % e)
            self.wsgi_server.stop()

        except Exception, e:
            log.error("Web server is shutting down from an unhandled" \
                      " exception: %s" % e)
            self.wsgi_server.stop()

    def stop(self):
        self.wsgi_server.stop()

class ClientSession(object):
    def __init__(self):
        self.id = unique_id()
        self.reset_csrf()

        self.created = datetime.now()
        self.visited = None

        self.attributes = dict()

    def check_owner(self, owner):
        user = self.attributes["login_session"].user.name
        return owner == user

    def get_csrf(self):
        return self.csrf

    def reset_csrf(self):
        self.csrf = unique_id()
        
    def __repr__(self):
        args = (self.__class__.__name__, self.id, self.created)
        return "%s(%s,%s)" % args

class ClientSessionExpireThread(Thread):
    def __init__(self, server):
        super(ClientSessionExpireThread, self).__init__()

        self.server = server
        self.name = self.__class__.__name__

        self.setDaemon(True)

    def run(self):
        while True:
            self.expire_sessions()
            time.sleep(60)

    def expire_sessions(self):
        when = datetime.now() - timedelta(hours=1)
        count = 0

        for session in self.server.client_sessions_by_id.values():
            if session.visited is not None and session.visited < when:
                try:
                    del self.server.client_sessions_by_id[session.id]
                    count += 1
                except KeyError:
                    pass

        log.info("Expired %i client sessions", count)
