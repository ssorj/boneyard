from ptolemy.common.messaging import *
from ptolemy.common.server import *
from ptolemy.harness import *

from timer import *
from worker import *

log = logging.getLogger("ptolemy.harnessserver")

class HarnessServer(PtolemyServer):
    def __init__(self, config, id):
        super(HarnessServer, self).__init__(config)

        self.id = id
        self.harness = HarnessServerHarness(self)

        self.messaging_thread = MessagingThread(self.config.broker)
        self.worker_thread = WorkerThread(self)

        self.expire_threshold = 86400 * 30

    def init(self):
        super(HarnessServer, self).init()

        self.harness.init()

        self.messaging_thread.init()
        self.worker_thread.init()

    def start(self):
        self.messaging_thread.start()
        self.worker_thread.start()

    def run(self):
        self.start()

        self.harness.update_model()

        while True:
            now = datetime.now()

            try:
                self.add_cycles(now)
            except:
                log.exception("Failed adding new cycles")

            try:
                self.expire_cycles(now)
            except:
                log.exception("Failed expiring old cycles")

            now = datetime.now()
            secs = 3600 - (now.minute * 60 + now.second)

            time.sleep(secs + 1)

    def add_cycles(self, now):
        log.debug("Adding new cycles")

        if now.hour == 0: # Midnight
            self.add_cycles_by_frequency("daily")

            if now.weekday() == 5: # Saturday
                self.add_cycles_by_frequency("weekly")

            if now.day == 1: # First day of the month
                self.add_cycles_by_frequency("monthly")

        if self.worker_thread.is_busy():
            log.info("Cycles in progress; skipping hourly work")
            return

        self.add_cycles_by_frequency("hourly")

    def add_cycles_by_frequency(self, frequency):
        model = self.harness.model

        for project in model.projects_by_name.values():
            tests = [x for x in project.tests_by_name.values()
                     if x.frequency == frequency]

            if not tests:
                continue

            for branch in project.branches_by_name.values():
                cycle = HarnessCycle(model, self.harness, branch, str(uuid4()))
                cycle.target_tests = tests

                log.info("Enqueueing %s", cycle)
                
                self.worker_thread.cycles.put(cycle)

    def expire_cycles(self, now):
        log.debug("Expiring old cycles")

        fn = lambda x: x.start_time
        cycles = sorted(self.harness.cycles_by_id.values(), key=fn)

        now = datetime_to_unixtime(now)

        for cycle in cycles:
            if cycle.start_time > now - self.expire_threshold:
                break

            try:
                cycle.delete()
            except:
                log.exception("Failed deleting %s", cycle)

class HarnessServerHarness(HarnessHarness):
    def __init__(self, server):
        super(HarnessServerHarness, self).__init__(server.id, server.home)

        self.server = server
    
    def update_model(self, cycle=None):
        log.warn("Updating model!")

        thread = self.server.messaging_thread
        model = self.server.harness.model
        message = Message(model.marshal(cycle))

        thread.send(ptolemy_model_update_address, message)
