from ptolemy.common.model import *

from util import *

log = logging.getLogger("ptolemy.harness.branch")

class HarnessBranch(Branch):
    def __init__(self, project, name, url):
        super(HarnessBranch, self).__init__(project, name)

        self.url = url

        base = self.project.branches_path
        self.path = os.path.join(base, self.name)

    def init(self):
        log.debug("Initializing %s", self)
