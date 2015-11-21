#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from disco import *
from qpid_management import *

_log = logger("main")
_strings = StringCatalog(__file__)

class Console(Application):
    def __init__(self, home):
        super(Console, self).__init__()

        self.home = home

        self.home_frame = HomeFrame(self, "home")
        self.file_frame = FileFrame(self, "file")

        dir = os.path.join(self.home, "web")
        self.file_frame.add_files_dir(dir)

        self.default_frame = self.home_frame

class HomeFrame(PageFrame):
    def __init__(self, app, name):
        super(HomeFrame, self).__init__(app, name)

        self.view_page = HomeView(self, "view")

        self.default_page = self.view_page

class HomeView(Page):
    def __init__(self, frame, name):
        super(HomeView, self).__init__(frame, name)

        self.modes = ModeSet(self, "modes")
        self.modes.add_mode(Overview(self, "overview"))
        self.modes.add_mode(Connections(self, "connections"))
        self.modes.add_mode(Addresses(self, "addresses"))
        self.modes.add_mode(Links(self, "links"))
        self.modes.add_mode(Nodes(self, "nodes"))

        self.tabs = ModeSetTabs(self, "tabs", self.modes)

    def get_title(self, session):
        return "Dispatch router"

    @xml
    def render_modes(self, session):
        return self.modes.render(session)

    @xml
    def render_tabs(self, session):
        return self.tabs.render(session)

class Overview(Widget):
    def __init__(self, page, name):
        super(Overview, self).__init__(page, name)

    def get_title(self, session):
        return "Overview"

    @xml
    def render_content(self, session):
        with ClientContext() as context:
            node = Node("$management")
            attrs = node.get_attributes(context)

        return html_elem("pre", fmt_dict(attrs))

class Connections(Table):
    def get_title(self, session):
        return "Connections"

    def get_header_titles(self, session):
        return ("Host", "State",
                "SASL mechanisms", "Role", "Direction")

    def get_data(self, session):
        with ClientContext() as context:
            node = Node("$management")

            type = "org.apache.qpid.dispatch.connection"
            attrs = ("host", "state",
                     "sasl", "role", "dir")

            response = node.query(context, type, attrs)

        return response["results"]

class Addresses(Table):
    def get_title(self, session):
        return "Addresses"

    def get_header_titles(self, session):
        return ("Name", "Subscribers", "Remotes",
                "Deliveries in", "Deliveries out", "Deliveries through")

    def get_data(self, session):
        with ClientContext() as context:
            node = Node("$management")

            type = "org.apache.qpid.dispatch.router.address"
            attrs = ("name", "suscriberCount", "remoteCount",
                     "deliveriesIngress", "deliveriesEgress",
                     "deliveriesTransit")

            response = node.query(context, type, attrs)

        return response["results"]

class Links(Table):
    def get_title(self, session):
        return "Links"

    def get_header_titles(self, session):
        return ("Name", "Type", "Direction",
                "Address", "Events", "Messages")

    def get_data(self, session):
        with ClientContext() as context:
            node = Node("$management")

            type = "org.apache.qpid.dispatch.router.link"
            attrs = ("name", "linkType", "linkDir",
                     "owningAddr", "eventFifoDepth", "msgFifoDepth")

            response = node.query(context, type, attrs)

        return response["results"]

class Nodes(Table):
    def get_title(self, session):
        return "Nodes"

    def get_header_titles(self, session):
        return ("Name", "Address", "Next hop",
                "Link", "Valid origins")

    def get_data(self, session):
        with ClientContext() as context:
            node = Node("$management")

            type = "org.apache.qpid.dispatch.router.node"
            attrs = ("name", "addr", "nextHop",
                     "routerLink", "validOrigins")

            response = node.query(context, type, attrs)

        return response["results"]

if "QPID_DISPATCH_DEBUG" in os.environ:
    setup_console_logging("debug")
else:
    setup_console_logging("info")

home = os.environ["QPID_DISPATCH_HOME"]

app = Console(home)

app.init()
app.start()

def application(env, start_response):
    return app.application(env, start_response)
