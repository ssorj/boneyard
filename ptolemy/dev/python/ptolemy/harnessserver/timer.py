from ptolemy.common.server import *
from ptolemy.harness.cycle import *

from worker import *

log = logging.getLogger("ptolemy.harnessserver.timer")

class TimerThread(ServerThread):
    def __init__(self, server):
        super(TimerThread, self).__init__(server, "timer")

    def run(self):
        self.enqueue_cycles("hourly")

        while True:
            now = datetime.now()
            secs = 3600 - (now.minute * 60 + now.second)
            then = now + timedelta(seconds=secs)

            log.info("Sleeping until %s", then.strftime("%H:%M"))

            time.sleep(secs + 1)

            if now.hour == 0:
                self.enqueue_cycles("daily")

                if now.weekday() == 5: # Saturday
                    self.enqueue_cycles("weekly")

                if now.day == 1: # First day of the month
                    self.enqueue_cycles("monthly")

            if self.server.worker_thread.is_busy():
                log.info("Cycles in progress; skipping hourly work")

                continue

            self.enqueue_cycles("hourly")

    def enqueue_cycles(self, frequency):
        model = self.server.model
        harness = self.server.harness

        for project in model.projects:
            tests = [x for x in project.tests if x.frequency == frequency]

            if not tests:
                continue

            for branch in project.branches:
                cycle = HarnessCycle(model, harness, branch, str(uuid4()))
                cycle.target_tests = tests

                log.info("Enqueueing %s", cycle)
                
                self.server.worker_thread.cycles.put(cycle)
