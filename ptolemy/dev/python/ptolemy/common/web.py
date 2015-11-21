from util import *
from wsgiserver import CherryPyWSGIServer

log = logging.getLogger("ptolemy.common.web")

class WebServer(object):
    http_date = "%a, %d %b %Y %H:%M:%S %Z"
    http_date_gmt = "%a, %d %b %Y %H:%M:%S GMT"

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.server = CherryPyWSGIServer \
            ((self.host, self.port), self.service_request)
        # XXX self.server.environ["wsgi.version"] = (1, 1)

    def start(self):
        self.server.start()

    def stop(self):
        self.server.stop()

    def service_request(self, env, response):
        pass

    def send_not_found(self, response, headers):
        message = "404 Not Found"

        headers.append(("Content-Length", str(len(message))))
        headers.append(("Content-Type", "text/plain"))

        response(message, headers)

        return (message,)

    def send_message(self, response, headers, message):
        headers.append(("Content-Length", str(len(message))))
        headers.append(("Content-Type", "text/plain"))

        response(message, headers)

        return (message,)

    def send_redirect(self, response, headers, url):
        headers.append(("Location", url))
        headers.append(("Content-Length", "0"))

        response("303 See Other", headers)

        return ()

    def send_not_modified(self, response, headers):
        headers.append(("Content-Length", "0"))

        response("304 Not Modified", headers)

        return ()

    def print_url_vars(self, query, writer):
        writer.write("URL variables:\n\n")

        if query:
            vars = query.split(";")

            for var in sorted(vars):
                key, value = var.split("=")
                writer.write("  %-30s  %s\n" % (key, value))

        writer.write("\n")

    def print_environment(self, env, writer):
        writer.write("Environment:\n\n")

        for key in sorted(env):
            value = env[key]

            writer.write("  %-30s  %s\n" % (key, value))

        writer.write("\n")
