import errno
import signal

from util import *

log = logging.getLogger("ptolemy.common.process")

class UnixProcess(object):
    def __init__(self, executable):
        self.executable = executable
        self.output = None
        self.args = list()

        self.pid = None
        self.exit_code = None
        self.exit_signal = None

    def start(self):
        try:
            self.do_start()
        except OSError:
            log.exception("Unexpected error")

    def do_start(self):
        assert self.pid is None, self.pid
        self.pid = os.fork()

        if self.pid == 0:
            # Child

            os.setpgid(0, 0)

            if self.output:
                os.dup2(self.output.fileno(), 1)
                os.dup2(self.output.fileno(), 2)

            os.execv(self.executable, [self.executable] + self.args)

            os._exit(255)

    def running(self):
        if self.exit_code is not None:
            return

        try:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
        except OSError, e:
            if e.errno == errno.ECHILD:
                return False

            log.exception("Unexpected error")
            return True

        if pid == 0:
            return True

        self.exit_code = os.WEXITSTATUS(status)
        self.exit_signal = os.WTERMSIG(status)

    def stop(self):
        if not self.running():
            return

        try:
            try:
                os.killpg(self.pid, signal.SIGTERM)
            except OSError:
                pass

            time.sleep(1)
        finally:
            if self.running():
                try:
                    os.killpg(self.pid, signal.SIGKILL)
                except OSError:
                    pass
        
        self.wait()

    def wait(self):
        if self.exit_code is not None:
            return

        try:
            pid, status = os.waitpid(self.pid, 0)
        except OSError:
            log.exception("Unexpected error")
            return

        self.exit_code = os.WEXITSTATUS(status)
        self.exit_signal = os.WTERMSIG(status)

    def __repr__(self):
        args = self.__class__.__name__, self.executable, self.pid
        return "%s(%s,%r)" % args
