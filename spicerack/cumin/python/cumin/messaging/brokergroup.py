from mint import *
from wooly import *
from wooly.widgets import *
from wooly.forms import *

from cumin.model import *
from cumin.widgets import *
from cumin.parameters import *
from cumin.sqladapter import *
from cumin.formats import *
from cumin.util import *

from broker import *

import main

strings = StringCatalog(__file__)

class BrokerGroupSelector(ObjectSelector):
    def __init__(self, app, name):
        cls = app.model.com_redhat_cumin_messaging.BrokerGroup

        super(BrokerGroupSelector, self).__init__(app, name, cls)

        frame = "main.messaging.brokergroup"
        col = ObjectLinkColumn(app, "name", cls.name, cls._id, frame)
        self.add_column(col)

        self.add_attribute_column(cls.description)

        self.remove = BrokerGroupSelectionRemove(app, self)

        task = BrokerGroupAdd(app)
        link = ObjectTaskLink(app, "brokergroupadd", task)
        self.links.add_child(link)

class BrokerGroupSelectionRemove(ObjectSelectorTask):
    def get_title(self, session):
        return "Remove"

    def do_invoke(self, invoc, group):
        conn = self.app.database.get_connection()

        try:
            cursor = conn.cursor()

            group.delete(cursor)

            conn.commit()
        finally:
            conn.close()

        invoc.end()

class BrokerGroupFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.com_redhat_cumin_messaging.BrokerGroup

        super(BrokerGroupFrame, self).__init__(app, name, cls)

        brokers = BrokerSelector(app, "brokers")
        brokers.group = self.object
        self.view.add_tab(brokers)

        self.edit = BrokerGroupEdit(app, self)
        self.remove = BrokerGroupRemove(app, self)

class BrokerGroupForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(BrokerGroupForm, self).__init__(app, name, task)

        self.name_ = self.NameField(app, "name")
        self.add_field(self.name_)

        self.description = self.Description(app, "description")
        self.add_field(self.description)

    class NameField(StringField):
        def render_title(self, session):
            return "Group Name"

    class Description(MultilineStringField):
        def render_title(self, session):
            return "Description"

class BrokerGroupAdd(ObjectTask):
    def __init__(self, app):
        super(BrokerGroupAdd, self).__init__(app)

        self.form = BrokerGroupAddForm(app, self.name, self)

    def get_title(self, session):
        return "Add broker group"

    def enter(self, session):
        nsession = wooly.Session(self.app.form_page)

        self.form.return_url.set(nsession, session.marshal())
        self.form.show(nsession)

        return nsession

    def do_invoke(self, invoc, obj, name, description):
        conn = self.app.database.get_connection()

        try:
            cursor = conn.cursor()

            cls = self.app.model.com_redhat_cumin_messaging.BrokerGroup
            group = cls.create_object(cursor)

            group.name = name
            group.description = description
            group.fake_qmf_values()

            group.save(cursor)

            conn.commit()
        finally:
            conn.close()

        invoc.description = "Add broker group '%s'" % name

        invoc.end()

class BrokerGroupAddForm(BrokerGroupForm):
    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            name = self.name_.get(session)
            description = ""

            self.task.invoke(session, None, name, description)
            self.task.exit_with_redirect(session)

    def render_title(self, session):
        return self.task.get_title(session)

class BrokerGroupEdit(ObjectFrameTask):
    def __init__(self, app, frame):
        super(BrokerGroupEdit, self).__init__(app, frame)

        self.form = BrokerGroupEditForm(app, self.name, self)

    def get_title(self, session):
        return "Edit"

    def do_invoke(self, invoc, group, name, description):
        assert group

        group.name = name
        group.description = description

        conn = self.app.database.get_connection()

        try:
            cursor = conn.cursor()

            group.save(cursor)

            conn.commit()
        finally:
            conn.close()

        invoc.end()

class BrokerGroupEditForm(BrokerGroupForm):
    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            group = self.object.get(session)
            name = self.name_.get(session)
            description = self.description.get(session)

            self.task.invoke(session, group, name, description)
            self.task.exit_with_redirect(session)

    def process_display(self, session):
        group = self.object.get(session)

        self.name_.set(session, group.name)
        self.description.set(session, group.description)

    def render_title(self, session):
        group = self.object.get(session)
        return self.task.get_description(session)

class BrokerGroupRemove(ObjectFrameTask):
    def get_title(self, session):
        return "Remove"

    def do_exit(self, session):
        self.app.main_page.main.messaging.view.show(session)

    def do_invoke(self, invoc, group):
        conn = self.app.database.get_connection()

        try:
            cursor = conn.cursor()

            group.delete(cursor)

            conn.commit()
        finally:
            conn.close()

        invoc.end()

class BrokerEngroup(ObjectFrameTask):
    def get_title(self, session):
        return "Add to groups"

    def do_invoke(self, invoc, broker, groups):
        print "XXX engroup", broker, groups

        invoc.end()

        return

        all_groups = BrokerGroup.select()
        selected_ids = [x.id for x in selected_groups]
        for group in all_groups:
            sql_sel = "broker_id=%i and broker_group_id=%i" % \
                (broker.id, group.id)
            existing_mapping = BrokerGroupMapping.select(sql_sel)
            if not group.id in selected_ids:
                if existing_mapping.count() > 0:
                    # remove mapping if group is not checked and there
                    # is already a mapping
                    existing_mapping[0].destroySelf()
            else:
                if existing_mapping.count() == 0:
                    # add mapping if group is checked but there
                    # is not already a mapping
                    new_mapping = BrokerGroupMapping(brokerID=broker.id,
                                                     brokerGroupID=group.id)
                    new_mapping.syncUpdate()
