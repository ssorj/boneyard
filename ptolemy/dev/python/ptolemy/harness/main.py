from model import *
from util import *

log = logging.getLogger("ptolemy.harness")

class HarnessHarness(Harness):
    def __init__(self, id, path):
        super(HarnessHarness, self).__init__(HarnessModel(self), id)

        self.path = path
        self.projects_path = os.path.join(self.path, "projects")
        self.branches_path = os.path.join(self.path, "branches")
        self.cycles_path = os.path.join(self.path, "cycles")

        self.file_server_url = None
        self.running_processes = set()

    def init(self):
        log.debug("Initializing %s", self)

        init_path(self.projects_path)
        init_path(self.branches_path)
        init_path(self.cycles_path)

        self.model.load()
        self.model.init()

        self.domain_name = get_domain_name()

        os_name, os_version = get_os_info()
        arch = get_host_arch()

        self.environment = Environment(self.model, os_name, os_version, arch)

        if self.file_server_url is None:
            self.file_server_url = "http://%s:10101" % self.domain_name

    def run(self, branch, tests=None, force=False):
        assert isinstance(branch, HarnessBranch), branch

        cycle = HarnessCycle(self.model, self, branch, str(uuid4()))
        cycle.force = force

        if tests:
            cycle.target_tests = tests

        cycle.run()

        return cycle

    def __repr__(self):
        args = self.__class__.__name__, self.path
        return "%s(%s)" % args

def get_os_info():
    try:
        return get_redhat_os_info()
    except:
        pass # more attempts

def get_redhat_os_info():
    release = load("/etc/redhat-release")
    tokens = release.split()
    return tokens[0], tokens[2]

def get_domain_name():
    return socket.gethostname()

def get_host_arch():
    return os.uname()[4]

def get_host_id():
    try:
        return get_redhat_host_id()
    except:
        pass # more attempts

def get_redhat_host_id():
    id = load("/var/lib/dbus/machine-id")
    id = id.strip()
    return id
