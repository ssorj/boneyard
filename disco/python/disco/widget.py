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

from .application import *
from .parameter import *

_log = logger("disco.widget")
_strings = StringCatalog(__file__)

class Widget(RenderObject):
    def __init__(self, page, name):
        super().__init__()

        self._page = page
        self._name = name

        self.content_template = RenderTemplate(self, "content")

        assert not self.app._initialized
        assert self.name not in self.page.widgets_by_name

        self.page.widgets.append(self)
        self.page.widgets_by_name[self.name] = self

    def delete(self):
        self.page.widgets.remove(self)
        del self.page.widgets_by_name[self.name]

    @property
    def page(self):
        return self._page

    @property
    def name(self):
        return self._name

    @property
    def frame(self):
        return self.page.frame
        
    @property
    def app(self):
        return self.page.app

    def init(self):
        super().init()

        self.bind_templates()

    def get_title(self, request):
        pass

    def render_content(self, request):
        pass

    def __repr__(self):
        path = "/{}/{}#{}".format(self.frame.name, self.page.name, self.name)
        return fmt_repr(self, path)

class ModeSet(Widget):
    def __init__(self, page, name):
        super().__init__(page, name)

        self.parameter = SymbolParameter(self.page, self.name)
        self.parameter.required = False

        self.modes = list()
        self.modes_by_name = dict()

        self.default_mode = None

    def add_mode(self, mode):
        assert not self.app._initialized 
        assert mode.name not in self.modes_by_name

        self.modes.append(mode)
        self.modes_by_name[mode.name] = mode

        if self.default_mode is None:
            self.default_mode = mode

    @xml
    def render_content(self, request):
        mode_name = self.parameter.get(request)
        mode = self.modes_by_name.get(mode_name, self.default_mode)

        return mode.render(request)

class ModeSetTabs(Widget):
    def __init__(self, page, name, mode_set):
        super().__init__(page, name)

        self._mode_set = mode_set

    @xml
    def render_content(self, request):
        selected_mode_name = self._mode_set.parameter.get(request)
        selected_mode = self._mode_set.modes_by_name.get \
                        (selected_mode_name, self._mode_set.default_mode)

        out = list()

        for mode in self._mode_set.modes:
            title = mode.get_title(request)
            selected = mode is selected_mode

            branch = request.branch()
            self._mode_set.parameter.set(branch, mode.name)
            href = branch.get_href()

            out.append(html_li(html_link(title, href, selected=selected)))

        return "".join(out)

class Table(Widget):
    def __init__(self, page, name):
        super().__init__(page, name)

    def get_header_titles(self, request):
        pass

    def get_data(self, request):
        pass

    @xml
    def render_headers(self, request):
        titles = self.get_header_titles(request)

        if titles is None:
            return

        out = list()
        out.append(html_open("tr"))

        for title in titles:
            out.append(html_th(xml_escape(str(title))))

        out.append(html_close("tr"))

        return "".join(out)

    @xml
    def render_data(self, request):
        data = self.get_data(request)

        if data is None:
            return

        out = list()

        for record in data:
            out.append(html_open("tr"))

            for item in record:
                out.append(html_td(xml_escape(str(item))))

            out.append(html_close("tr"))

        return "".join(out)
