import logging
import os
import random
import socket
import stat
import struct
import sys
import time

from UserDict import UserDict
from collections import deque
from datetime import datetime, timedelta
from ftplib import FTP
from gzip import GzipFile
from pprint import pprint, pformat
from shutil import copyfileobj
from smtplib import SMTP
from threading import Thread, Lock, Condition, Event, \
    enumerate as enumerate_threads
from traceback import print_exc

log = logging.getLogger("ptolemy.common.util")

try:
    from uuid import uuid4
except ImportError:
    class UUID:
        def __init__(self, hex=None, bytes=None):
            if [hex, bytes].count(None) != 1:
                raise TypeErrror("need one of hex or bytes")
            if bytes is not None:
                self.bytes = bytes
            elif hex is not None:
                fields = hex.split("-")
                fields[4:5] = [fields[4][:4], fields[4][4:]]
                args = [int(x,16) for x in fields]
                self.bytes = struct.pack("!LHHHHL", *args)

        def __cmp__(self, other):
            if isinstance(other, UUID):
                return cmp(self.bytes, other.bytes)
            else:
                return -1

        def __str__(self):
            args = struct.unpack("!LHHHHL", self.bytes)
            return "%08x-%04x-%04x-%04x-%04x%08x" % args

        def __repr__(self):
            return "UUID(%r)" % str(self)

        def __hash__(self):
            return self.bytes.__hash__()

    rand = random.Random()
    rand.seed((os.getpid(), time.time(), socket.gethostname()))

    def random_uuid():
        bytes = [rand.randint(0, 255) for i in xrange(16)]

        # From RFC4122, the version bits are set to 0100                                                                                                                       
        bytes[7] &= 0x0F
        bytes[7] |= 0x40

        # From RFC4122, the top two bits of byte 8 get set to 01                                                                                                               
        bytes[8] &= 0x3F
        bytes[8] |= 0x80

        return "".join(map(chr, bytes))

    def uuid4():
        return UUID(bytes=random_uuid())

try:
    from collections import defaultdict
except:
    class defaultdict(dict):
        def __init__(self, default_factory=None, *a, **kw):
            if (default_factory is not None and
                not hasattr(default_factory, '__call__')):
                raise TypeError('first argument must be callable')
            dict.__init__(self, *a, **kw)
            self.default_factory = default_factory

        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                return self.__missing__(key)

        def __missing__(self, key):
            if self.default_factory is None:
                raise KeyError(key)
            self[key] = value = self.default_factory()
            return value

        def __reduce__(self):
            if self.default_factory is None:
                args = tuple()
            else:
                args = self.default_factory,
            return type(self), args, None, None, self.items()

        def copy(self):
            return self.__copy__()

        def __copy__(self):
            return type(self)(self.default_factory, self)

        def __deepcopy__(self, memo):
            import copy
            return type(self)(self.default_factory,
                              copy.deepcopy(self.items()))

        def __repr__(self):
            return 'defaultdict(%s, %s)' % (self.default_factory,
                                            dict.__repr__(self))

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

format = "%Y-%m-%d %H:%M:%S"

def unixtime_to_datetime(utime):
    return datetime.fromtimestamp(utime)

def datetime_to_unixtime(dtime):
    return time.mktime(dtime.timetuple()) + 1e-6 * dtime.microsecond

def fmt_local_unixtime(utime=None):
    if utime is None:
        utime = time.time()

    return time.strftime(format + " %Z", time.localtime(utime))

def fmt_local_unixtime_medium(utime):
    return time.strftime("%d %b %H:%M", time.localtime(utime))

def fmt_local_unixtime_brief(utime):
    now = time.time()

    if utime > now - 86400:
        fmt = "%H:%M"
    else:
        fmt = "%d %b"

    return time.strftime(fmt, time.localtime(utime))

def load(*args):
    path = os.path.join(*args)

    if not os.path.exists(path):
        return

    try:
        file = open(path, "r")

        try:
            value = file.read()
        finally:
            file.close()
    except IOError:
        log.exception("Failed loading %s", path)

    value = value.strip()

    return value

def save(*args):
    path = os.path.join(*args[0:-1])
    value = args[-1]
    file = open(path, "w")

    try:
        file.write(value)
    finally:
        file.close()

def compress_file(inpath):
    outpath = "%s.gz" % inpath
    infile = open(inpath, "r")

    try:
        outfile = GzipFile(outpath, "wb")

        try:
            copyfileobj(infile, outfile)
        finally:
            outfile.close()
    finally:
        infile.close()

    os.remove(inpath)

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

def split_comma_list(string):
    return [x.strip() for x in string.split(",") if x != ""]

class ServerThread(Thread):
    def __init__(self, server, name):
        super(ServerThread, self).__init__()

        self.server = server
        self.name = name

        self.setDaemon(True)

    def init(self):
        pass

    def run(self):
        try:
            self.do_run()
        except KeyboardInterrupt:
            raise
        except:
            log.exception("Unexpected error")

    def do_run(self):
        while True:
            time.sleep(86400)

    def __repr__(self):
        args = self.__class__.__name__, self.server, self.name
        return "%s(%s,%s)" % args

def send_mail(from_address, to_addresses, body):
    smtp = SMTP()
    smtp.connect()

    try:
        smtp.sendmail(from_address, to_addresses, body)
    finally:
        smtp.quit()

def send_file(host, file):
    ftp = FTP()
    ftp.connect(host)

    head, tail = os.path.split(file.path)

    try:
        ftp.storbinary("STOR %s" % tail, file)
    finally:
        ftp.quit()

def print_threads(writer=sys.stdout):
    row = "%-28s  %-36s  %-18s  %-8s  %-8s  %s"

    writer.write(row % ("Class", "Name", "Ident", "Alive", "Daemon", ""))
    writer.write(os.linesep)
    writer.write("-" * 120)
    writer.write(os.linesep)

    for thread in sorted(enumerate_threads()):
        cls = thread.__class__.__name__
        name = thread.name
        ident = thread.ident
        alive = thread.is_alive()
        daemon = thread.daemon
        extra = ""
        #extra = thread._Thread__target

        writer.write(row % (cls, name, ident, alive, daemon, extra))
        writer.write(os.linesep)

def trunc(s, l):
    try:
        return s[:l]
    except IndexError:
        return s

_logging_modules = ("ptolemy",)

_logging_levels_by_name = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARN,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
    }

_logging_handlers_by_logger = defaultdict(list)

class PtolemyStreamHandler(logging.StreamHandler):
    def __repr__(self):
        args = self.__class__.__name__, self.level, self.stream.name
        return "%s(%s,%s)" % args

def add_logging(name, level, file):
    assert level, level
    assert file, file

    if isinstance(level, str):
        level = _logging_levels_by_name[level.lower()]

    if isinstance(file, str):
        file = open(file, "a")
 
    handler = PtolemyStreamHandler(file)

    fmt = "%(process)d %(asctime)s %(levelname)s %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    handler.setLevel(level)

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)

    _logging_handlers_by_logger[log].append(handler)

def clear_logging(name):
    log = logging.getLogger(name)

    handlers = _logging_handlers_by_logger[log]

    for handler in handlers:
        log.removeHandler(handler)

    del _logging_handlers_by_logger[log]

def print_logging(name):
    log = logging.getLogger(name)

    handlers = _logging_handlers_by_logger[log]

    for handler in handlers:
        print handler

def setup_initial_logging():
    log_level = "warn"

    if "PTOLEMY_DEBUG" in os.environ:
        log_level = "debug"

    for name in _logging_modules:
        add_logging(name, log_level, sys.stderr)

def setup_console_logging(config):
    for name in _logging_modules:
        clear_logging(name)

    log_level = config.log_level

    if "PTOLEMY_DEBUG" in os.environ:
        log_level = "debug"

    for name in _logging_modules:
        add_logging(name, log_level, sys.stderr)

def setup_server_logging(config):
    for name in _logging_modules:
        clear_logging(name)

    if "PTOLEMY_DEBUG" in os.environ:
        for name in _logging_modules:
            add_logging(name, "debug", sys.stderr)

    if config.log_file:
        for name in _logging_modules:
            add_logging(name, config.log_level, config.log_file)
