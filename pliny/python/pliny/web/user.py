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

from queue import *

_strings = StringCatalog(__file__)

class UserFrame(PageFrame):
    def __init__(self, app, name):
        super(UserFrame, self).__init__(app, name)

        self.view_page = UserView(self, "view")
        self.queue_create_page = QueueCreate(self, "queue-create")

        self.default_page = self.view_page

    def get_title(self, session, user=None):
        if user is None:
            user = session.user

        return "User %s" % user.name

    def get_href(self, session, user=None):
        if user is None:
            user = session.user

        args = self.name, url_escape(user.name)
        return "/%s/%s" % args

    def receive(self, request):
        try:
            user_name = request.path[1]
        except IndexError:
            return request.send_not_found()

        database = request.attributes["database_session"]
        user = database.get_user(user_name)

        if user is None:
            return request.send_not_found()

        request.attributes["user"] = user

        try:
            page_name = request.path[2]
        except IndexError:
            page_name = ""

        try:
            page = self.pages_by_name[page_name]
        except KeyError:
            return request.send_not_found()

        return page.receive(request)

    def process(self, session):
        session.user = session.request.attributes["user"]

class UserView(Page):
    @xml
    def render_title(self, session):
        return "User <em>%s</em>" % xml_escape(session.user.name)

    def render_queue_create_href(self, session):
        return self.frame.queue_create_page.get_href(session)

    @xml
    def render_queues(self, session):
        if not session.user.queues:
            return html_none()

        out = list()
        out.append(html_open("table", _class="object-list"))

        headers = list()
        headers.append(html_th("Name"))
        headers.append(html_th("Status"))
        headers.append(html_th("Access"))
        headers.append(html_th("URI"))

        out.append(html_tr("".join(headers)))

        for queue in sorted_by(session.user.queues):
            columns = list()

            name = xml_escape(queue.name)
            href = self.app.queue_frame.get_href(session, queue)
            columns.append(html_td(html_link(name, href)))

            status = init_cap(queue.status)
            columns.append(html_td(status))

            access = init_cap(queue.access)
            columns.append(html_td(access))

            uri = self.app.get_queue_uri(queue)
            columns.append(html_td(xml_escape(uri)))

            out.append(html_tr("".join(columns)))

        out.append(html_close("table"))
        return "".join(out)
