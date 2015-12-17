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

from .account import *

_log = logger("disco.demo")
_strings = StringCatalog(__file__)

class DemoApplication(Application):
    def __init__(self, home):
        super().__init__()

        self.home = home

        self.home_frame = HomeFrame(self, "home")
        self.file_frame = FileFrame(self, "file")

        self.default_frame = self.home_frame

class HomeFrame(PageFrame):
    def __init__(self, app, name):
        super().__init__(app, name)

        self.view_page = HomeView(self, "view")

        self.default_page = self.view_page

class HomeView(Page):
    def __init__(self, frame, name):
        super().__init__(frame, name)

        self.modes = ModeSet(self, "mode")
        self.modes.add_mode(Introduction(self, "intro"))
        self.modes.add_mode(Basics(self, "basics"))
        self.modes.add_mode(Tables(self, "tables"))

        self.tabs = ModeSetTabs(self, "tabs", self.modes)

    def get_title(self, request):
        return "Disco Demo"

    @xml
    def render_modes(self, request):
        return self.modes.render(request)

    @xml
    def render_tabs(self, request):
        return self.tabs.render(request)

class Introduction(Widget):
    def get_title(self, request):
        return "Introduction"

class Basics(Widget):
    def get_title(self, request):
        return "Basics"

class Tables(Widget):
    def __init__(self, page, name):
        super().__init__(page, name)

        self.table = NumberTable(page, "table")

    def get_title(self, request):
        return "Tables"

    @xml
    def render_table(self, request):
        return self.table.render(request)

class NumberTable(Table):
    def get_data(self, request):
        data = list()
        size = 12

        for i in range(size):
            row = list()

            for j in range(size):
                row.append(i * j)

            data.append(row)

        return data

setup_console_logging("info")

home = os.environ.get("DISCO_HOME", "/usr/share/disco")

app = DemoApplication(home)
app.init()
app.start()

def application(env, start_response):
    return app.application(env, start_response)
