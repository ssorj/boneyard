from wooly import *
from wooly.widgets import *
from wooly.resources import *

from cumin.main import CuminModule
from cumin.util import *

from broker import *
from brokergroup import *
from test import *

strings = StringCatalog(__file__)

class Module(CuminModule):
    def __init__(self, app, name):
        super(Module, self).__init__(app, name)

        self.frame = MessagingFrame(self.app, "messaging")
        self.frame.cumin_module = name

    def init(self):
        super(Module, self).init()

        self.app.main_page.main.messaging = self.frame
        self.app.main_page.main.add_tab(self.frame)

    def init_test(self, test):
        MessagingTest("messaging", test)

class MessagingFrame(CuminFrame):
    def __init__(self, app, name):
        super(MessagingFrame, self).__init__(app, name)

        self.view = MessagingView(app, "view")
        self.add_mode(self.view)

        self.broker = BrokerFrame(app, "broker")
        self.add_mode(self.broker)
        self.add_sticky_view(self.broker)

        self.broker_group = BrokerGroupFrame(app, "brokergroup")
        self.add_mode(self.broker_group)

        self.tasks = list()

    def init(self):
        super(MessagingFrame, self).init()

        for task in self.tasks:
            task.init()

    def render_title(self, session):
        return "Messaging"

class MessagingView(Widget):
    def __init__(self, app, name):
        super(MessagingView, self).__init__(app, name)

        heading = self.Heading(app, "heading")
        self.add_child(heading)

        self.tabs = TabbedModeSet(app, "tabs")
        self.add_child(self.tabs)

        self.tabs.add_tab(BrokerSelector(app, "brokers"))

    class Heading(CuminHeading):
        def render_title(self, session):
            return "Messaging"

        def render_icon_href(self, session):
            return "resource?name=broker-36.png"
