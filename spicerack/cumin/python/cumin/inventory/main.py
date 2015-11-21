from wooly import *
from wooly.widgets import *
from wooly.resources import *

from cumin.main import CuminModule
from cumin.widgets import *
from cumin.util import *

from system import *

strings = StringCatalog(__file__)

class Module(CuminModule):
    def __init__(self, app, name):
        super(Module, self).__init__(app, name)

        self.frame = InventoryFrame(app, "inventory")
        self.app = app
        self.frame.cumin_module = name

    def init(self):
        self.app.main_page.main.inventory = self.frame
        self.app.main_page.main.add_tab(self.frame)

class InventoryFrame(CuminFrame):
    def __init__(self, app, name):
        super(InventoryFrame, self).__init__(app, name)

        self.view = InventoryView(app, "view")
        self.add_mode(self.view)

        self.system = SystemFrame(app, "system")
        self.add_mode(self.system)

    def render_title(self, session):
        return "Inventory"

class InventoryView(Widget):
    def __init__(self, app, name):
        super(InventoryView, self).__init__(app, name)

        heading = self.Heading(app, "heading")
        self.add_child(heading)

        self.tabs = TabbedModeSet(app, "tabs")
        self.add_child(self.tabs)

        self.tabs.add_tab(SystemSelector(app, "systems"))

    class Heading(CuminHeading):
        def render_title(self, session):
            return "Inventory"

        def render_icon_href(self, session):
            return "resource?name=system-36.png"
