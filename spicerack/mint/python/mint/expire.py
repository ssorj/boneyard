from update import *
from util import *

log = logging.getLogger("mint.expire")

class ExpireThread(MintPeriodicProcessThread):
    def __init__(self, app, interval=3600, threshold=24*3600):
        super(ExpireThread, self).__init__(app, interval)

        self.threshold = threshold
        # Default for the package list is all the packages in the
        # model, but this may be set by the app
        self.packages = self.app.model._packages

        # If a specific class list is given, then self.packages
        # will be ignored and we will iterate over the classes
        self.classes = []

    def init(self):
        super(ExpireThread, self).init()

        log.debug("Expire interval is %i seconds", self.interval)
        log.debug("Expire threshold is %i seconds", self.threshold)

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
                log.debug("Periodic process %s exited" % self.getName())
                return
        finally:
            self._condition.release()

        super(ExpireThread, self).run()

    def process(self):
        threshold = self.threshold
        count = 0

        log.info("Starting expire")

        conn = self.app.database.get_connection()

        def loop_body(cls, cursor):
            count = 0
            if cls._storage == "none":
                return count

            values = {"seconds": threshold}
            if cls.sql_samples_delete is not None:
                cls.sql_samples_delete.execute(cursor, values)
                log.debug("Deleted %i samples %s", cursor.rowcount, cls)
                count = cursor.rowcount

            # For timestamp persistent classes, we get rid of the
            # objects in addition to the samples
            if hasattr(cls, "sql_timestamp_delete") and \
               cls.sql_timestamp_delete is not None:
                cls.sql_timestamp_delete.execute(cursor, values)
                log.debug("Deleted %i objects %s", cursor.rowcount, cls)
                count += cursor.rowcount

            conn.commit()
            return count

        try:
            cursor = conn.cursor()
            if len(self.classes) > 0:
                for cls in self.classes:
                    if self.stop_requested:
                        break
                    count += loop_body(cls, cursor)
            else:
                for pkg in self.packages:
                    for cls in pkg._classes:
                        if self.stop_requested:
                            break
                        count += loop_body(cls, cursor)
        finally:
            conn.close()
        log.info("Expired %i rows", count)
