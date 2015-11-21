from wooly import *
from wooly.widgets import *
from wooly.resources import *

from cumin.main import CuminModule
from cumin.objecttask import *
from cumin.util import *

from submission import *
from pool import *
from test import *

strings = StringCatalog(__file__)

class Module(CuminModule):
    def __init__(self, app, name):
        super(Module, self).__init__(app, name)

        self.job_submit = JobSubmit(app)
        self.dag_job_submit = DagJobSubmit(app)
        self.vm_job_submit = VmJobSubmit(app)

    def init(self):
        super(Module, self).init()

        self.frame = PoolFrame(self.app, "grid")
        self.frame.cumin_module = self.name

        self.app.main_page.main.grid = self.frame
        self.app.main_page.main.add_tab(self.frame)


    def init_test(self, test):
        GridTest("grid", test)
