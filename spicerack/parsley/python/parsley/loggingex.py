import logging
import os
import sys
from stat import ST_DEV, ST_INO

import select
from logging.handlers import RotatingFileHandler
from collectionsex import defaultdict
from threading import Thread
from time import sleep

_levels_by_name = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARN,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
    }

_handlers_by_logger = defaultdict(list)

def set_log_owner(file_obj):
    # If the current user is root, make sure
    # that the file has the same ownership
    # as the containing directory
    if os.getuid() == 0:
        try:
            dir_name = os.path.split(file_obj)[0]
            dir_stat = os.stat(dir_name)
            os.chown(file_obj, dir_stat.st_uid, dir_stat.st_gid)
        except:
            pass

class MyRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename, maxBytes, backupCount):
        RotatingFileHandler.__init__(self,
                                    filename, 
                                    maxBytes = maxBytes, 
                                    backupCount = backupCount)
        # Following snippett taken from WatchedFileHandler in Python 2.6.
        # Essentially, we need a hybrid between a RotatingFileHandler
        # and a WatchedFileHandler since we may have multiple rotaters all
        # logging to the same file.
        if not os.path.exists(self.baseFilename):
            self.dev, self.ino = -1, -1
        else:
            stat = os.stat(self.baseFilename)
            self.dev, self.ino = stat[ST_DEV], stat[ST_INO]

    def _reopen(self):
        """
        Reimplementation of FileHandler._open() from Python 2.6, because
        Python 2.4 does not have _open (and hence, it cannot be called)

        Open the current base file with the (original) mode and encoding.
        Return the resulting stream.
        """
        if self.encoding is None:
            stream = open(self.baseFilename, self.mode)
        else:
            stream = codecs.open(self.baseFilename, self.mode, self.encoding)
        return stream

    def emit(self, record):
        # Never want to crash writing out a log entry
        try:
            self._emit(record)
        except (KeyboardInterrupt, SystemExit):
            # We don't want to swallow these exceptions
            raise
        except Exception, e:
            sys.stderr.write("Warning, logging exception writing " + self.baseFilename + ", %s\n" % e)

    def _emit(self, record):
        # Following snippett taken from WatchedFileHandler in Python 2.6
        # Reopen the stream if the original file has been moved
        if not os.path.exists(self.baseFilename):
            stat = None
            changed = 1
        else:
            stat = os.stat(self.baseFilename)
            changed = (stat[ST_DEV] != self.dev) or (stat[ST_INO] != self.ino)
        if changed and self.stream is not None:
            try:
                self.stream.flush()
            except:
                pass
            try:
                self.stream.close()
            except:
                pass
            self.stream = self._reopen()
            if stat is None:
                stat = os.stat(self.baseFilename)
            self.dev, self.ino = stat[ST_DEV], stat[ST_INO]

        # Now that we've reopened the file if necessary, call the regular
        # emit() routine for the rotating handler.
        RotatingFileHandler.emit(self, record)

    def doRollover(self):
        RotatingFileHandler.doRollover(self)

        # Try to fix up permissions on new file
        set_log_owner(self.baseFilename)

def enable_logging(name, level, file_obj, max_MB = 0, max_archives = 0):
    assert level
    assert file_obj
    assert type(max_MB) in (float,int)
    assert type(max_archives) is int

    if type(level) is str:
        level = _levels_by_name[level.lower()]

    if type(file_obj) is str:
        # Assume file_obj is a path name.  If the file does not
        # exist try to create the file with the correct uid/gid 
        # based on the containing dir.
        if not os.path.exists(file_obj):
            open(file_obj, 'a+')
            set_log_owner(file_obj)
    
        handler = MyRotatingFileHandler(file_obj,
                                        maxBytes = max_MB * 1024 *1024,
                                        backupCount = max_archives)
    else:
        handler = logging.StreamHandler(file_obj)

    fmt = "%(process)d %(asctime)s %(levelname)s %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    handler.setLevel(level)

    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(handler)

    _handlers_by_logger[log].append(handler)

def disable_logging(name):
    log = logging.getLogger(name)

    handlers = _handlers_by_logger[log]

    for handler in handlers:
        log.removeHandler(handler)

class PipeLogThread(Thread):
    """
    Thread class for reading multiple file descriptors and redirecting to files.

    This class takes a list of file descriptors and a parallel list of paths.
    It opens the file descriptors for read and opens the paths for write.
    Via select(), it waits for a descriptor to become readable and then
    writes the content to the file at the corresponding path.

    If rollover_size is non-zero, the size of output files will be checked before each
    write.  If the file size is greater than or equal to the rollover_size, the file
    will be closed and reopened for write as an empty file.

    If call_on_fail is callable, it will be called if the thread gets an
    exception during the run() routine.  This is useful for notifying other threads
    that the thread has exited unexpectedly, potentially allowing them to clean up
    the IO being handled by this thread.
    """
    def __init__(self, descriptors, paths, call_on_fail=None, 
                 rollover_size = 1024*1024):

        assert len(descriptors) == len(paths)
        assert type(descriptors) in (list,tuple)
        assert type(paths) in (list,tuple)
        assert self.check_unique(descriptors)
        assert self.check_unique(paths)
        assert type(rollover_size) is int

        super(PipeLogThread, self).__init__()

        self.name = self.__class__.__name__
        self.immediate = False
        self.daemon = True
        self.rollover_size = rollover_size
        self.call_on_fail = call_on_fail

        # Open an output file at the designated path for each input descriptor
        self.descriptors = descriptors
        self.files = dict()
        for desc, path in zip(self.descriptors, paths):
            creating = not os.path.exists(path)
            f = open(path, "a")
            if creating:
                set_log_owner(path)
            self.files[desc] = [f, path]

        # Open a pipe for exit signaling
        self.stop_r, self.stop_w = os.pipe()

    def check_unique(self, values):
        return len(set(values)) == len(values)

    def check_rollover(self, file):
        if os.path.getsize(file[1]) >= self.rollover_size:
            file[0].close()
            file[0] = open(file[1], "w")

    def run(self):
        # The last thing we want is unhandled exceptions in this thread
        # which could leave IO broken.
        stop = False
        try:
            try:
                while not stop:
                    r, w, e = select.select(self.descriptors+[self.stop_r], [], [])

                    # If we have been told to stop immediately, do so.
                    if self.stop_r in r:
                        if self.immediate:
                            break
                        stop = True

                    for desc in r:
                        if desc != self.stop_r:
                            msg = os.read(desc,1024)
                            if msg != "":
                                if self.rollover_size != 0:
                                    self.check_rollover(self.files[desc])
                                    self.files[desc][0].write(msg)
                                    self.files[desc][0].flush()

            except Exception, e:
                if callable(self.call_on_fail):
                    self.call_on_fail()
            
        finally:
            for key, value in self.files.items():
                value[0].close()

    def stop(self, immediate=False):
        if self.isAlive():
            self.immediate = immediate
            os.write(self.stop_w,"\n")
            if immediate:
                return

            # This gives the thread a chance to write out
            # anything pending on an input pipe.
            for i in range(5):
                if not self.isAlive():
                    break
                sleep(1)
