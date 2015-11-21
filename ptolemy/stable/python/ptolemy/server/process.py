import logging
import os
import signal
import sys

from util import *

from time import time as unix_time, sleep

log = logging.getLogger("ptolemy.server.process")

class UnixProcess(object):
    def __init__(self, executable, args=[]):
        self.executable = executable
        self.args = args

        self.pid = None
        self.exit_code = None
        self.exit_signal = None

        self.deadline = None
        self.timeout_handler = lambda: None

    def kill(self):
        if self.exit_code is not None:
            return

        # Send SIGUSR1 to the parent script so we can capture the
        # process state of children in the output.

        try:
            os.kill(self.pid, signal.SIGUSR1)
        except OSError, e:
            log.exception(e)

        sleep(1)

        try:
            os.killpg(self.pid, signal.SIGTERM)
        except OSError, e:
            log.exception(e)

        sleep(1)

        try:
            os.killpg(self.pid, signal.SIGKILL)
        except OSError, e:
            pass

    def wait(self):
        if self.exit_code is not None:
            return

        try:
            pid, status = os.waitpid(self.pid, 0)

            self.exit_code = os.WEXITSTATUS(status)
            self.exit_signal = os.WTERMSIG(status)
        except OSError, e:
            log.exception(e)

    def poll(self):
        if self.exit_code is not None:
            return True

        try:
            pid, status = os.waitpid(self.pid, os.WNOHANG)

            if pid == self.pid:
                self.exit_code = os.WEXITSTATUS(status)
                self.exit_signal = os.WTERMSIG(status)

                return True
        except OSError, e:
            log.exception(e)

    def run(self, output):
        try:
            self.do_run(output)
        except OSError, e:
            log.exception(e)

    def do_run(self, output):
        self.pid = os.fork()

        if self.pid == 0:
            # Child

            os.setpgid(0, 0)

            os.dup2(output.fileno(), 1)
            os.dup2(output.fileno(), 2)

            os.execv(self.executable, [self.executable] + self.args)

            os._exit(255)

        # Parent

        while True:
            if self.deadline and unixtime_now() > self.deadline:
                self.timeout_handler()

            if self.poll():
                break

            sleep(1)

    def __str__(self):
        return "%s(%s,%r)" % \
            (self.__class__.__name__, self.executable, self.pid)

if __name__ == "__main__":
    enable_logging("ptolemy", "debug", sys.stdout)

    proc = UnixProcess("/usr/bin/vmstat", ["1"])

    def handler():
        print "too long!", proc
        proc.kill()
        proc.wait()

    proc.timeout = 3
    proc.timeout_handler = handler

    try:
        proc.run(sys.stdout)
    except KeyboardInterrupt:
        proc.kill()
        proc.wait()
