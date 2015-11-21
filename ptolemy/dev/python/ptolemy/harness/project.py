from ptolemy.common.model import *

from branch import *
from cycle import *
from script import *
from test import *
from util import *

log = logging.getLogger("ptolemy.harness.project")

class HarnessProject(Project):
    def __init__(self, model, name):
        super(HarnessProject, self).__init__(model, name)

        base = self.model.harness.projects_path
        self.path = os.path.join(base, self.name)

        self.config_path = os.path.join(self.path, "project.config")

        base = self.model.harness.branches_path
        self.branches_path = os.path.join(base, self.name)

        base = self.model.harness.cycles_path
        self.cycles_path = os.path.join(base, self.name)

        path = os.path.join(self.path, "timeout.script")
        self.timeout_script = Script(path)

    def load(self):
        log.info("Loading %s", self)

        file = open(self.config_path)

        try:
            config = yaml.load(file)
        finally:
            file.close()

        #pprint(config)

        for name, fields in config["branches"].items():
            name = str(name)
            url = fields["url"]
            branch = HarnessBranch(self, name, url)

        for name, fields in config["tests"].items():
            name = str(name)
            test = HarnessTest(self, name)

            if not fields:
                continue
            
            requires = fields.get("requires")

            if requires:
                if isinstance(requires, str):
                    requires = [requires]

                test.required_test_names = requires
                
            test.frequency = fields.get("frequency", test.frequency)

    def init(self):
        log.info("Initializing %s", self)

        for branch in self.branches_by_name.values():
            branch.init()

        for test in self.tests_by_name.values():
            test.init()
