from ptolemy.common.model import *
from ptolemy.common.messaging import *
from ptolemy.common.server import *

log = logging.getLogger("ptolemy.harnessserver.worker")

class WorkerThread(ServerThread):
    def __init__(self, server):
        super(WorkerThread, self).__init__(server, "worker")

        self.cycles = ConcurrentQueue()
        self.busy = False # XXX Use something from threading for this

    def is_busy(self):
        return self.busy or not self.cycles.empty()

    def do_run(self):
        while True:
            try:
                cycle = self.cycles.get(timeout=1)
            except ConcurrentEmpty:
                continue

            assert not self.busy
            self.busy = True

            try:
                cycle.run()

                if cycle.status_code == cycle.STATUS_UNCHANGED:
                    cycle.delete()
                    continue

                cycle.save()

                self.server.harness.update_model(cycle)
            finally:
                assert self.busy
                self.busy = False
