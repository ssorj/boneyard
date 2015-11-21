from ptolemy.common.model import *

from script import *
from util import *

log = logging.getLogger("ptolemy.harness.test")

class HarnessTest(Test):
    def __init__(self, project, name):
        super(HarnessTest, self).__init__(project, name)

        path = os.path.join(self.project.path, "%s.script" % self.name)
        self.script = TestScript(self, path)

        self.required_test_names = set()
        self.required_tests = set()

        self.frequency = "hourly"

    def init(self):
        log.info("Initializing %s", self)

        for name in self.required_test_names:
            try:
                self.required_tests.add(self.project.tests_by_name[name])
            except KeyError:
                raise Exception("Test '%s' not found" % name)

    def run(self, cycle):
        log.info("Running %s", self)

        if not self.script.exists():
            log.info("%s isn't there; skipping it", self.script)
            return

        output_file = "%s.out" % self.name
        output_path = os.path.join(cycle.path, output_file)

        result = HarnessTestResult(self, cycle)
        result.start_time = time.time()

        proc = self.script.run(output_path)

        result.end_time = time.time()
        result.exit_code = proc.exit_code
        result.exit_signal = proc.exit_signal

        if os.path.exists(output_path):
            if result.exit_code != 0:
                result.output_sample = get_file_sample(output_path)

            try:
                compress_file(output_path)
                result.output_file = "%s.gz" % output_file
            except:
                log.exception("Gzip failed")
                result.output_file = output_file

        return result

def get_file_sample(path):
    size = os.path.getsize(path)

    file = open(path)
    try:
        if size >= 2048:
            file.seek(size - 2048)

            lines = file.readlines()
            lines[0] = "[snip]\n"

            return "".join(lines)
        else:
            return file.read()
    finally:
        file.close()

class HarnessTestResult(TestResult):
    def __init__(self, test, cycle):
        super(HarnessTestResult, self).__init__(cycle, test)

class TestScript(Script):
    def __init__(self, test, path):
        super(TestScript, self).__init__(path)

        self.test = test

        self.warn_duration = 60 * 60
        self.max_duration = 60 * 60 + 30 * 60

    def warn(self, proc):
        timeout_script = self.test.project.timeout_script

        if not timeout_script.exists():
            log.info("No timeout script; skipping it")
            return

        timeout_script.run_file(proc.output)

    def add_running_process(self, proc):
        harness = self.test.project.model.harness
        harness.running_processes.add(proc)

    def remove_running_process(self, proc):
        harness = self.test.project.model.harness
        harness.running_processes.remove(proc)
