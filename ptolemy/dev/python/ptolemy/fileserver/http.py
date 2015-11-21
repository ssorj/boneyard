from SocketServer import ThreadingMixIn, TCPServer
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from shutil import copyfileobj

from ptolemy.common.server import *

log = logging.getLogger("ptolemy.fileserver.http")

class HttpThread(ServerThread):
    def __init__(self, server):
        super(HttpThread, self).__init__(server, "http")

        self.request_handler = _HttpRequestHandler
        self.request_handler.ptolemy_server = self.server

    def init(self):
        pass

    def run(self):
        addr = self.server.config.http_host, self.server.config.http_port

        log.debug("Binding to %s:%i" % addr)

        server = _HttpServer(addr, self.request_handler)
        server.daemon_threads = True
        server.serve_forever()

class _HttpServer(ThreadingMixIn, TCPServer, HTTPServer):
    pass

class _HttpRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        log.info("Handling request for '%s'", self.path)

        try:
            self.respond()
        except:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()

            print_exc(file=self.wfile)

    def respond(self):
        root_path = self.ptolemy_server.cycles_path

        if self.path == "/":
            self.send_dir(root_path)
        else:
            tokens = self.path[1:].split("/")
            uuid = self.get_uuid(tokens[0])

            if not uuid:
                uuid = tokens[0]

            file_path = os.path.join(root_path, uuid, *tokens[1:])

            log.info("File path is %s", file_path)
            
            if os.path.isdir(file_path):
                self.send_dir(file_path)
            elif os.path.isfile(file_path):
                self.send_file(file_path)
            else:
                raise Exception("File not found")

    def get_uuid(self, partial):
        cycles_path = self.ptolemy_server.cycles_path

        for name in os.listdir(cycles_path):
            if name.startswith(partial):
                return name

    def send_dir(self, file_path):
        path = self.path

        if path.endswith("/"):
            path = self.path[:-1]

        cycles_path = self.ptolemy_server.cycles_path
        links = list()

        for name in os.listdir(file_path):
            args = path, name, name
            links.append("<a href=\"%s/%s\">%s</a>" % args)

        content = "\n".join(links)

        self.send_html(content)

    def send_html(self, content):
        log.info("Sending index")

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        self.wfile.write("<html><head>")
        self.wfile.write("<title>%s</title>" % self.path)
        self.wfile.write("</head><body><pre>")
        self.wfile.write(content)
        self.wfile.write("</pre></body>")

    def send_file(self, ospath):
        log.info("Sending file")

        length = os.stat(ospath).st_size

        file = open(ospath)

        try:
            self.send_response(200)

            self.send_header("Content-Length", length)
            self.send_header("Content-Type", "text/plain")

            # XXX need to handle .tar.gz here; consider treating
            # .out.gz specially

            if ospath.endswith(".gz"):
                self.send_header("Content-Encoding", "gzip")

            self.end_headers()

            copyfileobj(file, self.wfile)
        finally:
            file.close()

    # Disable default server logging
    def log_message(self, format, *args):
        pass
