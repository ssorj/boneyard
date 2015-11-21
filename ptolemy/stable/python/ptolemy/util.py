import sys, os, stat, time, socket, fcntl, signal, logging

from random import randint
from datetime import datetime
from UserDict import UserDict
from shutil import copyfileobj
from gzip import GzipFile
from threading import Thread
from qpid.connection import *
from qpid.exceptions import *
from qpid.session import *
from qpid.util import *
from time import sleep

from time import time as unixtime_now

log = logging.getLogger("ptolemy.util")

try:
    from __builtin__ import sorted
except ImportError:
    def sorted(iterable, cmp=None):
        slist = list(iterable)
        slist.sort(cmp)
        return slist

try:
    from __builtin__ import reversed
except ImportError:
    # From http://www.python.org/dev/peps/pep-0322/
    def reversed(x):
        if hasattr(x, 'keys'):
            raise ValueError("mappings do not support reverse iteration")
        i = len(x)
        while i > 0:
            i -= 1
            yield x[i]

try:
    from __builtin__ import set
except ImportError:
    from sets import Set as set

def short_id():
    return "%08x" % randint(0, sys.maxint)

def long_id():
    return "%08x%08x" % (randint(0, sys.maxint), randint(0, sys.maxint))

format = "%Y-%m-%d %H:%M:%S"

def unixtime_to_datetime(utime):
    return datetime.fromtimestamp(utime)

def datetime_to_unixtime(dtime):
    return time.mktime(dtime.timetuple()) + 1e-6 * dtime.microsecond

def fmt_local_unixtime(utime=None):
    if utime is None:
        utime = unixtime_now()

    return time.strftime(format + " %Z", time.localtime(utime))

def fmt_local_unixtime_medium(utime):
    return time.strftime("%d %b %H:%M", time.localtime(utime))

def fmt_local_unixtime_brief(utime):
    now = unixtime_now()

    if utime > now - 86400:
        fmt = "%H:%M"
    else:
        fmt = "%d %b"

    return time.strftime(fmt, time.localtime(utime))

def load(*args):
    path = os.path.join(*args)
    file = open(path, "r")
    try:
        value = file.read()
    finally:
        file.close()
    return value

def save(*args):
    path = os.path.join(*args[0:-1])
    value = args[-1]
    file = open(path, "w")
    try:
        file.write(value)
    finally:
        file.close()

def make_gzipped_copy(inpath, outpath):
    infile = open(inpath, "r")

    try:
        outfile = GzipFile(outpath, "wb")

        try:
            copyfileobj(infile, outfile)
        finally:
            outfile.close()
    finally:
        infile.close()

class Properties(UserDict):
    def __init__(self, *args):
        UserDict.__init__(self)

        self.path = os.path.join(*args)

    def load(self):
        if not os.path.exists(self.path):
            return

        file = open(self.path, "r")
        try:
            for line in file.readlines():
                try:
                    name, value = line[:-1].split(" ", 1)
                    self[name] = value
                except:
                    pass
        finally:
            file.close()

    def save(self):
        file = open(self.path, "w")
        try:
            for name, value in self.iteritems():
                if value:
                    file.write("%s %s\n" % (name, value))
        finally:
            file.close()

class QpidSessionThread(Thread):
    def __init__(self, addr):
        """
        addr = ("host", port)
        """

        super(QpidSessionThread, self).__init__()

        self.addr = addr

        self.setDaemon(True)

    def run(self):
        while True:
            log.info("Connecting to broker at %s:%i", *self.addr)

            conn = self.try_to_connect()

            log.debug("Connected")

            conn.start()
            session = conn.session(long_id())

            try:
                while True:
                    try:
                        self.do_run(session)
                    except SessionDetached:
                        raise
                    except Closed:
                        raise
                    except:
                        log.exception("Unexpected error")
                        sleep(1)
            except SessionDetached:
                log.debug("Session detached")

                continue
            except Closed:
                log.debug("Connection closed")

                continue

    def try_to_connect(self):
        timeout = 1

        while True:
            try:
                sock = connect(*self.addr)
                return Connection(sock)
            except socket.error:
                if timeout < 1024:
                    timeout = timeout * 2

                    log.info("Can't connect; retrying in %i seconds" \
                                 % timeout)

                time.sleep(timeout)

    def do_run(self, session):
        raise Exception("Not implemented")

levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARN,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
    }

def enable_logging(name, level, file):
    assert level
    assert file

    if type(level) is str:
        level = levels[level.lower()]

    if type(file) is str:
        file = open(file, "a")

    handler = logging.StreamHandler(file)

    fmt = "%(process)d %(asctime)s %(levelname)s %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    handler.setLevel(level)

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)

class PtolemyMessage(object):
    def __init__(self):
        self.destination = None
        self.routing_key = None
        self.response_queue = None
        self.headers = dict()
        self.body = None

    def set(self, name, value):
        self.headers[name] = value

    def get(self, name, default=None):
        return self.headers.get(name, default)

    def send(self, session):
        assert self.destination
        assert self.routing_key

        message = self.marshal(session)

        session.message_transfer(destination=self.destination,
                                 message=message)

    def marshal(self, session):
        dprops = session.delivery_properties(routing_key=self.routing_key)

        mprops = session.message_properties(application_headers=self.headers)
        mprops.reply_to = session.reply_to("amq.direct", self.response_queue)

        message = Message(dprops, mprops, self.body)

        return message

    def unmarshal(self, message):
        mprops = message.get("message_properties")

        self.headers.update(mprops.application_headers)
        self.body = message.body
        self.response_queue = mprops.reply_to.routing_key
