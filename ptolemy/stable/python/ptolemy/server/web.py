import logging
import os
import socket

from Queue import Queue as ConcurrentQueue, Empty, Full
from SocketServer import ThreadingMixIn, TCPServer
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from shutil import copyfileobj
from threading import Thread
from traceback import print_exc
from StringIO import StringIO

from model import *
from util import *

log = logging.getLogger("ptolemy.server.web")

class WebThread(ServerThread):
    def __init__(self, server):
        super(WebThread, self).__init__(server, "web")

        self.request_handler = RequestHandler
        self.request_handler.ptolemy_server = self.server

    def init(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.bind(self.server.web_addr)
        finally:
            s.close()

    def run(self):
        server = ThreadingHTTPServer \
            (self.server.web_addr, self.request_handler)
        server.daemon_threads = True
        server.serve_forever()

class ThreadingHTTPServer(ThreadingMixIn, TCPServer, HTTPServer):
    pass

class RequestHandler(BaseHTTPRequestHandler):
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
        path = self.path.strip("/")

        if path:
            ospath = os.path.join(self.ptolemy_server.cycles_path, path)
        else:
            ospath = self.ptolemy_server.cycles_path

        if os.path.isfile(ospath):
            self.send_file(ospath)
        elif os.path.isdir(ospath):
            self.send_index(ospath, path)
        else:
            raise Exception("File not found")

    def send_index(self, ospath, path):
        log.info("Sending index")

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        args = (self.ptolemy_server.name, path)

        self.wfile.write("<html><head>")
        self.wfile.write("<title>%s %s</title>" % args)
        self.wfile.write("</head><body><pre>")

        if path:
            path = "%s/%s" % (self.ptolemy_server.url, path)
            self.wfile.write("<a href=\"%s/..\">[..]</a>\n" % path)
        else:
            path = self.ptolemy_server.url

        for name in sorted(os.listdir(ospath)):
            args = (path, name, name)
            self.wfile.write("<a href=\"%s/%s\">%s</a>\n" % args)

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
