from qpid.messaging import *
from util import *

ptolemy_model_update_address = \
    "ptolemy.model.update; {create: always, node: {type: topic}}"
ptolemy_model_request_address = \
    "ptolemy.model.request; {create: always}"
ptolemy_model_response_address_fmt = \
    "ptolemy.model.response.%s; {create: always}"

log = logging.getLogger("ptolemy.common.model")

class Model(object):
    """
    Encompasses the nature and state of things that Ptolemy cares
    about
    """

    def __init__(self):
        self.harnesses_by_id = dict()
        self.harnesses_by_short_id = dict()

        self.projects_by_name = dict()

        self.cycles_by_id = dict()
        self.cycles_by_short_id = dict()

        self.environments = set()
        self.branches_by_key = dict()

        self.lock = Lock()

    def marshal(self, cycle=None):
        harnesses = list()
        projects = list()
        cycles = list()

        if cycle:
            harnesses.append(cycle.harness.marshal())
            projects.append(cycle.branch.project.marshal())
            cycles.append(cycle.marshal())
        else:
            for harness in self.harnesses_by_id.values():
                harnesses.append(harness.marshal())

            for project in self.projects_by_name.values():
                projects.append(project.marshal())

            for cycle in self.cycles_by_id.values():
                cycles.append(cycle.marshal())

        data = {
            "projects": projects,
            "harnesses": harnesses,
            "cycles": cycles,
            }

        return data

    def unmarshal(self, data):
        for harness_data in data["harnesses"]:
            id = harness_data["id"]

            try:
                harness = self.harnesses_by_id[id]
            except KeyError:
                harness = Harness(self, id)

            harness.unmarshal(harness_data)

        for project_data in data["projects"]:
            name = project_data["name"]

            try:
                project = self.projects_by_name[name]
            except KeyError:
                project = Project(self, name)

            project.unmarshal(project_data)

        for cycle_data in data["cycles"]:
            id = cycle_data["id"]

            try:
                cycle = self.cycles_by_id[id]
            except KeyError:
                harness = self.harnesses_by_id[cycle_data["harness_id"]]
                branch = self.branches_by_key[cycle_data["branch_key"]]

                cycle = Cycle(self, harness, branch, id)

            cycle.unmarshal(cycle_data)

    def fetch_update(self, session, timeout=1):
        address = ptolemy_model_response_address_fmt % str(uuid4())
        receiver = session.receiver(address)

        message = Message()
        message.reply_to = address

        sender = session.sender(ptolemy_model_request_address)
        sender.send(message)

        try:
            message = receiver.fetch(timeout=timeout)
        except Empty:
            return

        session.acknowledge()

        self.unmarshal(message.content)

    def __repr__(self):
        return self.__class__.__name__

class Project(object):
    """
    A software project
    """

    def __init__(self, model, name):
        assert isinstance(model, Model), model
        assert isinstance(name, basestring), name

        self.model = model
        self.name = name

        self.model.lock.acquire()
        
        try:
            self.model.projects_by_name[self.name] = self
        finally:
            self.model.lock.release()

        self.branches_by_name = dict()
        self.tests_by_name = dict()

    def marshal(self):
        tests = list()
        branches = list()

        for test in self.tests_by_name.values():
            tests.append(test.marshal())

        for branch in self.branches_by_name.values():
            branches.append(branch.marshal())

        data = {
            "name": self.name,
            "tests": tests,
            "branches": branches,
            }

        return data

    def unmarshal(self, data):
        for test_data in data["tests"]:
            name = test_data["name"]

            try:
                test = self.tests_by_name[name]
            except KeyError:
                test = Test(self, name)
            
            test.unmarshal(test_data)

        for branch_data in data["branches"]:
            name = branch_data["name"]

            try:
                branch = self.branches_by_name[name]
            except KeyError:
                branch = Branch(self, name)

            branch.unmarshal(branch_data)

    def __repr__(self):
        args = self.__class__.__name__, self.name
        return "%s(%s)" % args

class Test(object):
    """
    A test of a particular function of a project
    """

    def __init__(self, project, name):
        assert isinstance(project, Project), project
        assert isinstance(name, basestring), name

        self.project = project
        self.name = name

        self.project.model.lock.acquire()

        try:
            self.project.tests_by_name[self.name] = self
        finally:
            self.project.model.lock.release()

    def marshal(self):
        data = {
            "name": self.name,
            }

        return data

    def unmarshal(self, data):
        pass

    def __repr__(self):
        args = self.__class__.__name__, self.project, self.name
        return "%s(%s,%s)" % args

class Branch(object):
    """
    A branch of the source code of a software project
    """

    def __init__(self, project, name):
        assert isinstance(project, Project), project
        assert isinstance(name, basestring), name

        self.project = project
        self.name = name

        args = self.project.name, self.name
        self.key = "%s/%s" % args

        self.project.model.lock.acquire()

        try:
            self.project.branches_by_name[self.name] = self
            self.project.model.branches_by_key[self.key] = self
        finally:
            self.project.model.lock.release()

        self.cycles_by_id = dict()
        self.cycles_by_harness = defaultdict(set)

        self.last_cycle_by_environment = dict()

    def marshal(self):
        data = {
            "name": self.name,
            }

        return data

    def unmarshal(self, data):
        pass

    def __repr__(self):
        args = self.__class__.__name__, self.project, self.name
        return "%s(%s,%s)" % args

class Cycle(object):
    """
    A run of tests against a revision of a branch
    """

    STATUS_RUNNING = 100
    STATUS_PASSED = 200
    STATUS_UNCHANGED = 400
    STATUS_FAILED = 500

    def __init__(self, model, harness, branch, id):
        assert isinstance(model, Model), model
        assert isinstance(harness, Harness), harness
        assert isinstance(branch, Branch), branch
        assert isinstance(id, basestring), id

        self.model = model
        self.harness = harness
        self.branch = branch

        self.id = id
        self.short_id = trunc(self.id, 8)

        self.model.lock.acquire()

        try:
            self.model.cycles_by_id[self.id] = self
            self.model.cycles_by_short_id[self.short_id] = self

            self.branch.cycles_by_id[self.id] = self
            self.harness.cycles_by_id[self.id] = self
        finally:
            self.model.lock.release()

        self.url = None

        self.revision = None
        self.changes = None

        self.start_time = None
        self.end_time = None

        self.status_code = None
        self.status_message = None

        self.test_results_by_test = dict()

    def init(self):
        log.debug("Initializing %s", self)

        self.model.lock.acquire()

        try:
            env = self.harness.environment
            last = self.branch.last_cycle_by_environment.get(env)

            if last is None or last.start_time < self.start_time:
                self.branch.last_cycle_by_environment[env] = self
        finally:
            self.model.lock.release()

    def delete(self):
        self.model.lock.acquire()

        try:
            del self.model.cycles_by_id[self.id]
            del self.model.cycles_by_short_id[self.short_id]

            del self.branch.cycles_by_id[self.id]
            del self.harness.cycles_by_id[self.id]

            del self.branch.last_cycle_by_environment[self.harness.environment]
        finally:
            self.model.lock.release()

    def result_signature(self):
        tokens = list()

        tokens.append(str(self.status_code))

        for result in sorted(self.test_results_by_test.values()):
            tokens.append(str(result.exit_code))
            tokens.append(str(result.exit_signal))

        return ",".join(tokens)

    def is_news(self):
        antecedent = None

        for cycle in reversed(self.model.cycles):
            if cycle is self:
                continue

            if cycle.harness is self.harness and cycle.branch is self.branch:
                antecedent = cycle
                break

        if not antecedent:
            log.debug("%s isn't news: no antecedent", self)
            return False

        result = self.result_signature()
        last_result = antecedent.result_signature()

        if result == last_result:
            log.debug("%s isn't news: identical result (%s)", self, result)
            return False

        return True

    def marshal(self):
        test_results = list()

        for test_result in self.test_results_by_test.values():
            test_results.append(test_result.marshal())

        data = {
            "id": self.id,
            "harness_id": self.harness.id,
            "branch_key": self.branch.key,
            "url": self.url,
            "revision": self.revision,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status_code": self.status_code,
            "status_message": self.status_message,
            "changes": self.changes,
            "test_results": test_results,
            }

        return data

    def unmarshal(self, data):
        self.url = data["url"]
        self.revision = data["revision"]

        self.start_time = data["start_time"]
        self.end_time = data["end_time"]
        
        self.status_code = data["status_code"]
        self.status_message = data["status_message"]

        self.changes = data["changes"]

        for result_data in data["test_results"]:
            test_name = result_data["test_name"]
            test = self.branch.project.tests_by_name[test_name]

            try:
                result = self.test_results_by_test[test]
            except KeyError:
                result = TestResult(self, test)

            result.unmarshal(result_data)

        self.init()

    def __repr__(self):
        args = self.__class__.__name__, self.branch, self.id
        return "%s(%s,%s)" % args

class Harness(object):
    def __init__(self, model, id):
        assert isinstance(model, Model), model
        assert id is not None

        self.model = model
        self.id = id
        self.short_id = trunc(self.id, 8)

        self.model.lock.acquire()

        try:
            self.model.harnesses_by_id[self.id] = self
            self.model.harnesses_by_short_id[self.short_id] = self
        finally:
            self.model.lock.release()

        self.domain_name = None
        self.environment = None

        self.cycles_by_id = dict()

    def update_model(self, cycle):
        pass

    def marshal(self):
        data = {
            "id": self.id,
            "domain_name": self.domain_name,
            "environment": self.environment.marshal(),
            }

        return data

    def unmarshal(self, data):
        self.id = data["id"]
        self.domain_name = data["domain_name"]
        self.environment = Environment.unmarshal \
            (self.model, data["environment"])

    def __repr__(self):
        args = self.__class__.__name__, self.id
        return "%s(%s)" % args

class Environment(object):
    """
    A value object for classifying environment types
    """
    def __init__(self, model, os_name, os_version, arch):
        self.model = model
        self.os_name = os_name
        self.os_version = os_version
        self.arch = arch

        self._key = self.os_name, self.os_version, self.arch

        self.model.lock.acquire()

        try:
            self.model.environments.add(self)
        finally:
            self.model.lock.release()

    @classmethod
    def unmarshal(cls, model, data):
        os_name, os_version, arch = data.split(":", 2)
        return Environment(model, os_name, os_version, arch)

    def marshal(self):
        return ":".join(self._key)
        
    def __eq__(self, other):
        return self._key == other._key

    def __hash__(self):
        return id(self._key)

    def __repr__(self):
        args = self.__class__.__name__, ",".join(self._key)
        return "%s(%s)" % args
    
    def __str__(self):
        return "%s %s %s" % self._key

class TestResult(object):
    """
    The outcome of a test invocation
    """

    def __init__(self, cycle, test):
        self.cycle = cycle
        self.test = test

        self.cycle.model.lock.acquire()

        try:
            self.cycle.test_results_by_test[self.test] = self
        finally:
            self.cycle.model.lock.release()

        self.start_time = None
        self.end_time = None
        self.exit_code = None
        self.exit_signal = None
        self.output_file = None
        self.output_sample = None

    def marshal(self):
        data = {
            "test_name": self.test.name,
            "start_time": self.start_time,
            "end_time": self.start_time,
            "exit_code": self.exit_code,
            "exit_signal": self.exit_signal,
            "output_file": self.output_file,
            "output_sample": self.output_sample,
            }
        
        return data

    def unmarshal(self, data):
        self.start_time = data["start_time"]
        self.end_time = data["end_time"]
        self.exit_code = data["exit_code"]
        self.exit_signal = data["exit_signal"]
        self.output_file = data["output_file"]
        self.output_sample = data["output_sample"]

    def __repr__(self):
        args = (self.__class__.__name__,
                self.test.name,
                self.start_time, self.end_time,
                self.exit_code, self.exit_signal)

        return "%s(%s,%s,%s,%i,%i)" % args
