from cumin.main import CuminModule
from cumin.util import *

from widgets import *

strings = StringCatalog(__file__)

class Module(CuminModule):
    def init(self):
        super(Module, self).init()

        self.app.user_grid_page = MainPage(self.app, "usergrid.html")
        self.app.add_page(self.app.user_grid_page, add_to_link_set=True)
        self.app.user_grid_page.cumin_module = self.name
