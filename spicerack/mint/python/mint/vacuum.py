from update import *
from util import *

log = logging.getLogger("mint.vacuum")

class VacuumThread(MintPeriodicProcessThread):
    def __init__(self, app):
        super(VacuumThread, self).__init__(app, 60 * 60)
        self.processing_vacuum = False

    def init(self):
        super(VacuumThread, self).init()

        log.debug("Vacuum interval is %i seconds", self.interval)

    def run(self):
        if self.interval >= 60 * 60:
            interval = 0.25 * self.interval
        else:
            interval = self.interval

        try:
            self._condition.acquire()
            if not self.stop_requested:
                self._condition.wait(interval)
            if self.stop_requested:
                return
        finally:
            self._condition.release()

        super(VacuumThread, self).run()

    def stop(self, timeout=5):
        try:
            self._condition.acquire()
            self.stop_requested = True
            self._condition.notify()
            if self.processing_vacuum:
                timeout = None # forever
                log.info("Waiting for vacuum to finish")
        finally:
            self._condition.release()
        if self.isAlive():
            self.join(timeout)
        log.info("%s stopped" % self.getName())

    def process(self):
        self._condition.acquire()
        if self.stop_requested:
            self._condition.release()
            return

        # Flag this so the main thread can
        # know what we're doing
        self.processing_vacuum = True
        self._condition.release()

        log.info("Starting vacuum")

        conn = self.app.database.get_connection()
        conn.set_isolation_level(0)
        try:
            cursor = conn.cursor()
            cursor.execute("vacuum analyze")
        finally:
            conn.close()

        self._condition.acquire()
        self.processing_vacuum = False
        self._condition.release()

        log.info("Finished vacuum")
