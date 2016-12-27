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

from common import *

_strings = StringCatalog(__file__)

class HomeFrame(PageFrame):
    def __init__(self, app, name):
        super(HomeFrame, self).__init__(app, name)

        self.view_page = HomeView(self, "view")

        self.default_page = self.view_page

class HomeView(Page):
    def get_title(self, session):
        return "Pliny"

    def do_process(self, session):
        account = self.get_account(session)

        if account is not None:
            return self.app.user_frame.get_href(session, account.user)

    @xml
    def render_users(self, session):
        users = session.database.query(User).order_by("name")

        if not users:
            return html_none()

        out = list()
        out.append(html_open("ul"))

        for user in users:
            name = xml_escape(user.name)
            href = self.app.user_frame.get_href(session, user)

            out.append(html_li(html_link(name, href)))

        out.append(html_close("ul"))
        return "".join(out)
