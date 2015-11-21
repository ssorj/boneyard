from ptolemy.common.model import *

from project import *
from util import *

log = logging.getLogger("ptolemy.harness.model")

class HarnessModel(Model):
    def __init__(self, harness):
        super(HarnessModel, self).__init__()

        self.harness = harness

    def load(self):
        log.info("Loading %s", self)

        for name in sorted(os.listdir(self.harness.projects_path)):
            if name.startswith(".") or name == "common":
                continue

            project = HarnessProject(self, name)

            try:
                project.load()
            except:
                if "PTOLEMY_DEBUG" in os.environ:
                    log.exception("Failed loading %s", project)
                else:
                    log.warn("Failed loading %s", project)

        cycles_path = self.harness.cycles_path

        for id in os.listdir(cycles_path):
            if id.startswith("."):
                continue

            try:
                self.load_cycle(id)
            except:
                if "PTOLEMY_DEBUG" in os.environ:
                    log.exception("Failed loading cycle %s", id)
                else:
                    log.warn("Failed loading cycle %s", id)

    def load_cycle(self, id):
        cycles_path = self.harness.cycles_path
        path = os.path.join(cycles_path, id, "ptolemy", "attributes")

        file = open(path, "r")
        try:
            data = yaml.load(file)
        finally:
            file.close()

        key = data["branch_key"]
        branch = self.branches_by_key[key]

        cycle = HarnessCycle(self, self.harness, branch, id)
        cycle.load()

    def init(self):
        log.debug("Initializing %s", self)

        for project in self.projects_by_name.values():
            project.init()

        for cycle in self.cycles_by_id.values():
            cycle.init()

    def get_host_id(self):
        try:
            return self.get_redhat_host_id()
        except:
            pass # more attempts

    def get_redhat_host_id(self):
        host_id = load("/var/lib/dbus/machine-id")
        host_id = host_id.strip()
        return host_id
