from ptolemy.common.model import *

from test import *
from util import *

log = logging.getLogger("ptolemy.harness.cycle")

class HarnessCycle(Cycle):
    def __init__(self, model, harness, branch, id):
        super(HarnessCycle, self).__init__(model, harness, branch, id)

        path = self.harness.cycles_path
        self.path = os.path.join(path, self.id)

        args = self.harness.file_server_url, id[:8]
        self.url = "%s/%s" % args

        self.target_tests = None
        self.force = False

    def load(self):
        log.debug("Loading %s", self)

        path = os.path.join(self.path, "ptolemy", "attributes")

        file = open(path, "r")
        try:
            self.unmarshal(yaml.load(file))
        finally:
            file.close()

    def load_revision(self):
        self.revision = load(self.path, "ptolemy", "revision")

    def load_changes(self):
        self.changes = load(self.path, "ptolemy", "changes")

    def save(self):
        log.debug("Saving %s", self)

        path = os.path.join(self.path, "ptolemy", "attributes")

        file = open(path, "w")
        try:
            file.write(yaml.dump(self.marshal()))
        finally:
            file.close()

    def delete(self):
        log.debug("Deleting %s", self)

        for root, dirs, files in os.walk(self.path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        os.rmdir(self.path)

        super(HarnessCycle, self).delete()

    def run(self):
        log.info("Running %s", self)

        target_tests = self.target_tests

        if target_tests is None:
            target_tests = self.branch.project.tests

        init_path(os.path.join(self.path, "ptolemy"))

        self.setup_script_environment()

        self.status_code = 100
        self.status_message = "running"

        self.start_time = time.time()

        try:
            self.visit_tests(target_tests)

            message = "passed"

            log.info("Status: %s", message)

            self.status_code = self.STATUS_PASSED
            self.status_message = message
        except StatusUnchanged:
            message = "unchanged"
            
            log.info("Status: %s", message)

            self.status_code = self.STATUS_UNCHANGED
            self.status_message = message
        except StatusFailed:
            results = [x for x in self.test_results if x.exit_code != 0]
            count = len(results)

            if count == 1:
                message = "%s failed" % results[0].test.name
            else:
                message = "%i tests failed" % count

            log.info("Status: %s", message)

            self.status_code = self.STATUS_FAILED
            self.status_message = message

        self.end_time = time.time()

        self.load_revision()
        self.load_changes()

    def setup_script_environment(self):
        os.environ["PTOLEMY_HOME"] = self.branch.project.model.harness.path
        os.environ["PTOLEMY_PROJECT"] = self.branch.project.path
        os.environ["PTOLEMY_BRANCH"] = self.branch.path
        os.environ["PTOLEMY_BRANCH_URL"] = self.branch.url
        os.environ["PTOLEMY_CYCLE"] = self.path

        os.chdir(self.path)

    def visit_tests(self, tests):
        visited = set()
        failed = set()

        def visit(test):
            if test in visited:
                return

            visited.add(test)

            #log.debug("Visiting %s", test)

            for req in sorted(test.required_tests):
                visit(req)

                if req in failed:
                    failed.add(test)
                    return

            self.status_message = "running %s" % test.name

            result = test.run(self)

            if result is None:
                return

            self.check_status()

            if result.exit_code != 0:
                failed.add(test)

        for test in tests:
            visit(test)

        if failed:
            raise StatusFailed()

    def check_status(self):
        path = os.path.join(self.path, "ptolemy", "status")

        if not os.path.exists(path):
            return

        status = load(path)
        status = status.strip()

        try:
            exc = _status_exceptions_by_name[status]
        except KeyError:
            return

        if self.force and exc is StatusUnchanged:
            return

        raise exc()

class StatusDisabled(Exception):
    pass

class StatusUnchanged(Exception):
    pass

class StatusFailed(Exception):
    pass

_status_exceptions_by_name = {
    "disabled": StatusDisabled,
    "unchanged": StatusUnchanged,
}
