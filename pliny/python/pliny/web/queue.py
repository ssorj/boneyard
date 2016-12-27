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

_distribution_modes = {
    "single": "Single receiver",
    "fan_out": "Fan out",
    "round_robin": "Round robin",
    "lowest_cost": "Lowest cost",
}

class QueueFrame(PageFrame):
    def __init__(self, app, name):
        super(QueueFrame, self).__init__(app, name)

        self.view_page = QueueView(self, "view")
        self.edit_page = QueueEdit(self, "edit")
        self.delete_page = QueueDelete(self, "delete")
        self.delete_complete_page = QueueDeleteComplete \
            (self, "delete-complete")
        self.provision_page = QueueProvision(self, "provision")
        self.unprovision_page = QueueUnprovision(self, "unprovision")

        self.default_page = self.view_page

    def get_title(self, session):
        return "Queue %s" % session.queue.name

    def get_href(self, session, queue=None):
        if queue is None:
            queue = session.queue

        queue_name = url_escape(queue.name)
        args = self.name, queue_name

        return "/%s/%s" % args

    def receive(self, request):
        try:
            queue_name = request.path[1]
        except IndexError:
            return request.send_not_found()

        database = request.attributes["database_session"]
        queue = database.get_queue(queue_name)

        if queue is None:
            return request.send_not_found()

        request.attributes["queue"] = queue

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
        session.queue = session.request.attributes["queue"]

class QueueView(Page):
    def get_page_navigation_items(self, session):
        items = list()

        title = self.app.get_title(session)
        href = self.app.get_href(session)
        items.append((title, href))

        user = session.queue.user
        title = self.app.user_frame.get_title(session, user)
        href = self.app.user_frame.get_href(session, user)
        items.append((title, href))

        title = self.frame.get_title(session)
        href = self.frame.get_href(session)
        items.append((title, href))

        return items

    @xml
    def render_title(self, session):
        return "Queue <em>%s</em>" % xml_escape(session.queue.name)

    def render_queue_uri(self, session):
        return self.app.get_queue_uri(session.queue)

    def render_edit_href(self, session):
        return self.frame.edit_page.get_href(session, session.queue)

    def render_delete_href(self, session):
        return self.frame.delete_page.get_href(session, session.queue)

    def render_provision_href(self, session):
        return self.frame.provision_page.get_href(session, session.queue)

    def render_provision_disabled(self, session):
        if session.queue.status == "provisioned":
            return "disabled"

    def render_unprovision_href(self, session):
        return self.frame.unprovision_page.get_href(session, session.queue)

    def render_unprovision_disabled(self, session):
        if session.queue.status == "unprovisioned":
            return "disabled"

    @xml
    def render_properties(self, session):
        queue = session.queue
        user_href = self.app.user_frame.get_href(session, queue.user)
        distribution_mode = _distribution_modes[queue.distribution_mode]

        props = (
            ("Name", xml_escape(queue.name)),
            ("Access", init_cap(queue.access)),
            ("Distribution mode", distribution_mode),
        )

        return html_property_list(props)

    @xml
    def render_status_properties(self, session):
        queue = session.queue

        props = (
            ("Status", init_cap(queue.status)),
        )

        return html_property_list(props)

class QueueProvision(FormPage):
    def __init__(self, frame, name):
        super(QueueProvision, self).__init__(frame, name)

        self.continue_button.disabled = True

        self.exit_button.delete()
        self.exit_button = None

    def get_title(self, session):
        return "Provisioning queue %s" % session.queue.name

    def get_href(self, session, queue=None):
        args = self.frame.get_href(session, queue), self.name
        return "%s/%s" % args

    @xml
    def render_title(self, session):
        return "Provisioning queue <em>%s</em>" % xml_escape(session.queue.name)

    def process_continue(self, session):
        queue = session.queue

        with session.database:
            queue.status = "provisioned"

        msg = "Queue %s is provisioned" % queue.name
        self.set_result_message(session, msg)

        return self.frame.get_href(session)

class QueueUnprovision(QueueProvision):
    def get_title(self, session):
        return "Unprovisioning queue %s" % session.queue.name

    @xml
    def render_title(self, session):
        name = xml_escape(session.queue.name)
        return "Unprovisioning queue <em>%s</em>" % name

    def process_continue(self, session):
        queue = session.queue

        with session.database:
            queue.status = "unprovisioned"

        msg = "Queue %s is unprovisioned" % queue.name
        self.set_result_message(session, msg)

        return self.frame.get_href(session)

class QueueForm(FormPage):
    def __init__(self, frame, name):
        super(QueueForm, self).__init__(frame, name)

        self.name_input = StringInput(StringParameter(self, "name"))
        self.name_input.title = "Name"

        self.access_input = _AccessSelector \
            (SymbolParameter(self, "access"))
        self.access_input.title = "Access"
        self.access_input.default_value = "private"

        self.distribution_mode_input = _DistributionModeSelector \
            (SymbolParameter(self, "distribution_mode"))
        self.distribution_mode_input.title = "Distribution mode"
        self.distribution_mode_input.default_value = "single"

    def check_name_is_available(self, session):
        user = session.user
        name = self.name_input.get(session)
        query = session.database.query(Queue)
        existing = query.filter(Queue.name == name).first()

        if existing:
            msg = "Queue '%s' already exists" % name
            self.name_input.add_error(session, msg)

class _AccessSelector(RadioSelector):
    def get_items(self, session):
        yield SelectorItem("private", "private", "Private")
        yield SelectorItem("public", "public", "Public")

class _DistributionModeSelector(RadioSelector):
    def get_items(self, session):
        description = "Single receiver - Allow only one receiver at a time"
        yield SelectorItem("single", "single", description)

        description = "Fan out - Deliver a copy to each receiver"
        yield SelectorItem("fan_out", "fan_out", description)

        description = "Round robin - Balance deliveries evenly among receivers"
        yield SelectorItem("round_robin", "round_robin", description)

        description = "Lowest cost - Give priority to closer receivers"
        yield SelectorItem("lowest_cost", "lowest_cost", description)

class QueueCreate(QueueForm):
    def get_title(self, session):
        return "Create queue"

    def get_href(self, session, exit=None):
        path = super(FormPage, self).get_href(session)

        if exit is None:
            exit = session.request.uri

        return encode_href(path, exit=exit)

    def process_continue(self, session):
        user = session.user

        name = self.name_input.get(session)
        access = self.access_input.get(session)
        distribution_mode = self.distribution_mode_input.get(session)

        self.check_name_is_available(session)
        self.check_errors(session)

        with session.database:
            queue = Queue()
            queue.name = name
            queue.user = user
            queue.access = access
            queue.distribution_mode = distribution_mode

            session.database.add(queue)

        return self.app.queue_frame.provision_page.get_href(session, queue)

class QueueEdit(QueueForm):
    def __init__(self, page, name):
        super(QueueEdit, self).__init__(page, name)

        self.name_input.delete()
        self.name_input = HiddenInput(StringParameter(self, "name"))

    def get_title(self, session):
        return "Edit queue %s" % session.queue.name

    def get_href(self, session, queue=None):
        args = self.frame.get_href(session, queue), self.name
        return "%s/%s" % args

    @xml
    def render_title(self, session):
        return "Edit queue <em>%s</em>" % xml_escape(session.queue.name)

    def process_view(self, session):
        queue = session.queue

        self.name_input.set(session, queue.name)
        self.access_input.set(session, queue.access)
        self.distribution_mode_input.set(session, queue.distribution_mode)

    def process_continue(self, session):
        queue = session.queue
        access = self.access_input.get(session)
        distribution_mode = self.distribution_mode_input.get(session)

        self.check_errors(session)

        with session.database:
            queue.access = access
            queue.distribution_mode = distribution_mode

        return self.frame.provision_page.get_href(session)

class QueueDelete(ConfirmForm):
    def get_title(self, session):
        return "Delete queue %s" % session.queue.name

    def get_href(self, session, queue=None):
        args = self.frame.get_href(session, queue), self.name
        return "%s/%s" % args

    @xml
    def render_title(self, session):
        return "Delete queue <em>%s</em>" % xml_escape(session.queue.name)

    def process_continue(self, session):
        return self.frame.delete_complete_page.get_href(session)

class QueueDeleteComplete(QueueUnprovision):
    def process_continue(self, session):
        queue = session.queue
        user = queue.user

        with session.database:
            session.database.delete(queue)

        msg = "Queue %s is deleted" % queue.name
        self.set_result_message(session, msg)

        return self.app.user_frame.get_href(session, user=user)
