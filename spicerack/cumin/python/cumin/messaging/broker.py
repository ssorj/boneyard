from mint import *
from wooly import *
from wooly.widgets import *
from random import random
from psycopg2 import IntegrityError

from cumin.formats import *
from cumin.objectframe import *
from cumin.objecttask import *
from cumin.parameters import *
from cumin.sqladapter import *
from cumin.util import *
from cumin.widgets import *

from queue import *
from exchange import *
from brokerlink import *
from connection import *

from brokerlink import LinkSet

strings = StringCatalog(__file__)

class BrokerData(ObjectSqlAdapter):
    def __init__(self, app):
        vhost = app.model.org_apache_qpid_broker.Vhost
        broker = app.model.org_apache_qpid_broker.Broker
        system = app.model.org_apache_qpid_broker.System
        cluster = app.model.org_apache_qpid_cluster.Cluster
        mapping = app.model.com_redhat_cumin_messaging.BrokerGroupMapping

        super(BrokerData, self).__init__(app, vhost)

        self.add_join(broker, vhost.brokerRef, broker._id)
        self.add_join(system, broker.systemRef, system._id)
        self.add_outer_join(cluster, broker._id, cluster.brokerRef)

        subquery = SqlQuery(mapping.sql_table)
        this = mapping.sql_table._group_id
        that = "%(group_id)s"

        filter = SqlComparisonFilter(this, that)
        subquery.add_filter(filter)

        text = subquery.emit(("1",))

        self.group_filter = SqlExistenceFilter(text)

    def get_sql_options(self, options):
        sql_options = super(BrokerData, self).get_sql_options(options)

        if "group" in options.attributes:
            sql_options.filters.append(self.group_filter)

        return sql_options

class BrokerSelector(ObjectSelector):
    def __init__(self, app, name):
        # Actually a vhost selector, as it happens

        vhost = app.model.org_apache_qpid_broker.Vhost
        broker = app.model.org_apache_qpid_broker.Broker
        system = app.model.org_apache_qpid_broker.System
        cluster = app.model.org_apache_qpid_cluster.Cluster

        super(BrokerSelector, self).__init__(app, name, broker)

        self.table.adapter = BrokerData(app)

        self.group = SessionAttribute(self, "group")

        frame = "main.messaging.broker"
        col = ObjectLinkColumn(app, "name", broker.name, vhost._id, frame)
        self.add_column(col)

        self.add_attribute_column(system.nodeName)
        self.add_attribute_column(broker.port)
        self.add_attribute_column(cluster.clusterName)

    def get_data_values(self, session):
        values = super(BrokerSelector, self).get_data_values(session)

        group = self.group.get(session)

        if group:
            values["group_id"] = group._id

        return values

    def get_data_options(self, session):
        options = super(BrokerSelector, self).get_data_options(session)

        group = self.group.get(session)

        if group:
            options.attributes["group"] = True

        return options

class BrokerFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.org_apache_qpid_broker.Vhost

        super(BrokerFrame, self).__init__(app, name, cls)

        self.icon_href = "resource?name=broker-36.png"

        self.broker = SessionAttribute(self, "broker")

        self.queue = QueueFrame(app, "queue", self.object)
        self.add_mode(self.queue)

        self.exchange = ExchangeFrame(app, "exchange", self.object)
        self.add_mode(self.exchange)

        self.binding = BindingFrame(app, "binding", self.object)
        self.add_mode(self.binding)

        self.connection = ConnectionFrame(app, "connection", self.object)
        self.add_mode(self.connection)

        self.brokerlink = BrokerLinkFrame(app, "link", self.broker)
        self.add_mode(self.brokerlink)

        self.view = ObjectView(app, "view", self.broker)
        self.replace_child(self.view)

        self.view.add_tab(QueueSelector(app, "queues", self.object))
        self.view.add_tab(ExchangeSelector(app, "exchanges", self.object))
        self.view.add_tab(ConnectionSelector(app, "connections", self.object))
        self.view.add_tab(BrokerLinkSelector(app, "brokerlinks", self.object))
        self.view.add_tab(BrokerAccessControl(app, "accessControl", self.object))
        self.view.add_tab(BrokerClustering(app, "clustering", self.object))

        self.queue_add = QueueAdd(app, self)
        self.exchange_add = ExchangeAdd(app, self)
        self.brokerlink_add = BrokerLinkAdd(app, self)
        self.move_messages = MoveMessages(app, self)
        #self.engroup = BrokerEngroup(app, self)

    def get_title(self, session):
        return self.broker.get(session).name

    def do_process(self, session):
        super(BrokerFrame, self).do_process(session)

        vhost = self.object.get(session)

        cls = self.app.model.org_apache_qpid_broker.Broker
        obj = cls.get_object(session.cursor, _id=vhost._brokerRef_id)

        assert obj

        self.broker.set(session, obj)

class ModuleNotEnabled(Widget):
    def do_render(self, session):
        return "This module is not enabled"

class BrokerAccessControl(ModeSet):
    def __init__(self, app, name, vhost):
        super(BrokerAccessControl, self).__init__(app, name)

        self.vhost = vhost

        self.acl = self.AclModuleAttribute(self, "acl")
        self.add_attribute(self.acl)

        mode = ModuleNotEnabled(app, "notenabled")
        self.add_mode(mode)

        self.view = ObjectView(app, "view", self.acl)
        self.add_mode(self.view)

    class AclModuleAttribute(Attribute):
        def get_default(self, session):
            vhost = self.widget.vhost.get(session)

            cls = self.widget.app.model.org_apache_qpid_acl.Acl
            acl = cls.get_object(session.cursor, _brokerRef_id=vhost._brokerRef_id)
            return acl

    def do_process(self, session):
        if self.acl.get(session):
            self.view.show(session)

    def render_title(self, session):
        return "Access Control"

class BrokerClustering(ModeSet):
    def __init__(self, app, name, vhost):
        super(BrokerClustering, self).__init__(app, name)

        self.vhost = vhost

        self.cluster = self.ClusteringModuleAttribute(self, "cluster")
        self.add_attribute(self.cluster)

        self.notenabled = ModuleNotEnabled(app, "notenabled")
        self.add_mode(self.notenabled)

        self.view = ObjectView(app, "view", self.cluster)
        self.add_mode(self.view)

    class ClusteringModuleAttribute(Attribute):
        def get_default(self, session):
            vhost = self.widget.vhost.get(session)

            cls = self.widget.app.model.org_apache_qpid_cluster.Cluster
            cluster = cls.get_object(session.cursor, _brokerRef_id=vhost._brokerRef_id)
            return cluster

    def do_process(self, session):
        if self.cluster.get(session):
            self.view.show(session)

    def render_title(self, session):
        return "Clustering"

class BrokerBrowser(Widget):
    def __init__(self, app, name):
        super(BrokerBrowser, self).__init__(app, name)

        self.group_tmpl = WidgetTemplate(self, "group_html")

        self.brokers = BrokerSelector(app, "brokers")
        self.add_child(self.brokers)

    def render_title(self, session, *args):
        return "Brokers"

    def render_clear_filters_href(self, session):
        branch = session.branch()
        self.brokers.group.set(branch, None)
        return branch.marshal()

    def render_group_filters(self, session):
        cls = self.app.model.com_redhat_cumin_messaging.BrokerGroup
        groups = cls.get_selection(session.cursor)
        return self._render_filters(session, groups, self.group_tmpl)

    def render_group_link(self, session, group):
        return self._render_filter_link(session, group, self.brokers.group)

    def _render_filters(self, session, collection, template):
        writer = Writer()

        for object in collection:
            template.render(writer, session, object)

        template.render(writer, session, None)

        return writer.to_string()

    def _render_filter_link(self, session, object, param):
        branch = session.branch()
        param.set(branch, object)
        href = branch.marshal()

        name = object and object.name or "Any"
        name = xml_escape(name)

        class_ = param.get(session) is object and "selected"

        return fmt_link(href, name, class_)

class TopBrokerSet(CuminTable):
    def __init__(self, app, name):
        super(TopBrokerSet, self).__init__(app, name)

        col = self.NameColumn(app, "name")
        self.add_column(col)
        self.set_default_column(col)

    class NameColumn(SqlTableColumn):
        def render_title(self, session):
            return "Name"

        def render_content(self, session, data):
            reg = Identifiable(data["id"])
            href = self.page.main.messaging.broker.get_href(session, reg)
            return fmt_link(href, fmt_shorten(data["name"]))

class BrokerEngroupTaskForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(BrokerEngroupTaskForm, self).__init__(app, name, task)

        group = NewBrokerGroupParameter(app, "group")
        self.groups = self.Groups(app, "groups", group)
        self.add_field(self.groups)

    def do_process(self, session):
        super(BrokerEngroupTaskForm, self).do_process(session)

        vhost = self.object.get(session)

        cls = self.app.model.com_redhat_cumin_messaging.BrokerGroupMapping
        mappings = cls.get_selection(session.cursor, _broker_id=vhost._brokerRef_id)
        checked_groups = [x._group_id for x in mappings]
        self.groups.inputs.set(session, checked_groups)

    def process_submit(self, session):
        vhost = self.object.get(session)
        cls = self.app.model.org_apache_qpid_broker.Broker
        broker = cls.get_object_by_id(session.cursor, vhost._brokerRef_id)
        groups = self.groups.get(session)

        self.task.invoke(session, broker, groups)
        self.task.exit_with_redirect(session)

    class Groups(CheckboxItemSetField):
        def render_title(self, session):
            return "Groups"

        def do_get_items(self, session):
            cls = self.app.model.com_redhat_cumin_messaging.BrokerGroup
            groups = cls.get_selection(session.cursor)
            return (FormInputItem(x._id, title=x.name) for x in groups)

class BrokerEngroup(ObjectFrameTask):
    def __init__(self, app, selector):
        super(BrokerEngroup, self).__init__(app, selector)

        self.form = BrokerEngroupTaskForm(app, "engroup", self)

    def get_title(self, session):
        return "Add to groups"

    def do_invoke(self, invoc, broker, groups):
        conn = self.app.database.get_connection()

        try:
            cursor = conn.cursor()

            cls = self.app.model.com_redhat_cumin_messaging.BrokerGroup
            all_groups = cls.get_selection(cursor)
            selected_ids = [x._id for x in groups]

            cls = self.app.model.com_redhat_cumin_messaging.BrokerGroupMapping

            for group in all_groups:
                existing_mapping = cls.get_selection \
                    (cursor, _broker_id=broker._id, _group_id=group._id)
                if not group._id in selected_ids:
                    if len(existing_mapping) > 0:
                        existing_mapping[0].delete(cursor)
                else:
                    if len(existing_mapping) == 0:
                        new_mapping = cls.create_object(cursor)
                        new_mapping._broker_id = broker._id
                        new_mapping._group_id = group._id
                        new_mapping.fake_qmf_values()
                        new_mapping.save(cursor)

            conn.commit()
        finally:
            conn.close()

        invoc.end()
