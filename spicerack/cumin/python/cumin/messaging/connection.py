from wooly import *
from wooly.widgets import *
from wooly.tables import *

from cumin.objectframe import *
from cumin.objectselector import *
from cumin.objecttask import *
from cumin.stat import *
from cumin.widgets import *
from cumin.parameters import *
from cumin.formats import *
from cumin.util import *

import main

strings = StringCatalog(__file__)

class ConnectionFrame(ObjectFrame):
    def __init__(self, app, name, vhost):
        cls = app.model.org_apache_qpid_broker.Connection

        super(ConnectionFrame, self).__init__(app, name, cls)

        self.icon_href = "resource?name=client-36.png"

        self.session = SessionFrame(app, "session")
        self.add_mode(self.session)

        self.overview = ConnectionOverview(app, "overview", self.object)
        self.view.add_tab(self.overview)

        self.view.add_tab(SessionSelector(app, "sessions", self.object))

        self.close = ConnectionClose(app, self)

class ConnectionClose(ObjectFrameTask):
    def get_title(self, session):
        return "Close"

    def do_invoke(self, invoc, conn):
        # XXX generalize this check and use it for other closes

        mgmt_conns = set()

        for broker in self.app.session.qmf_brokers:
            # str(broker.conn) gets the broker.conn.sock host:port
            mgmt_conns.add(str(broker.conn))

        if conn.address in mgmt_conns:
            raise Exception \
                ("Cannot close management connection %s" % conn.address)

        self.app.remote.qmf.close(conn, invoc.make_callback())

class ConnectionSelector(ObjectSelector):
    def __init__(self, app, name, vhost):
        cls = app.model.org_apache_qpid_broker.Connection

        super(ConnectionSelector, self).__init__(app, name, cls)

        self.vhost = vhost

        frame = "main.messaging.broker.connection"
        col = ObjectLinkColumn(app, "address", cls.address, cls._id, frame)
        self.add_column(col)

        col = ConnectionProcessColumn \
            (app, "process", cls.remoteProcessName, cls.remotePid)
        self.add_column(col)
        self.add_search_filter(col)

        self.add_attribute_column(cls.authIdentity)
        self.add_attribute_column(cls.SystemConnection)
        self.add_attribute_column(cls.federationLink)
        self.add_attribute_column(cls.bytesFromClient)
        self.add_attribute_column(cls.bytesToClient)

        self.close = ConnectionSelectionClose(app, self)

        self.enable_csv_export(vhost)

class ConnectionSelectionClose(ObjectSelectorTask):
    def get_title(self, session):
        return "Close"

    def do_invoke(self, invoc, conn):
        # XXX generalize this check and use it for other closes

        mgmt_conns = set()

        for broker in self.app.session.qmf_brokers:
            # str(broker.conn) gets the broker.conn.sock host:port
            mgmt_conns.add(str(broker.conn))

        if conn.address in mgmt_conns:
            raise Exception \
                ("Cannot close management connection %s" % conn.address)

        self.app.remote.qmf.close(conn, invoc.make_callback())

    def get_item_content(self, session, item):
        args = (item.remoteProcessName, item.remotePid)
        if args[1] is None:
            return xml_escape(item.address)
        return xml_escape("%s (%i)" % args)

class ConnectionProcessColumn(ObjectTableColumn):
    def __init__(self, app, name, attr, pid_attr):
        super(ConnectionProcessColumn, self).__init__(app, name, attr)

        self.pid_attr = pid_attr

    def init(self):
        super(ConnectionProcessColumn, self).init()

        try:
            self.pid_field = self.table.adapter.fields_by_attr[self.pid_attr]
        except KeyError:
            self.pid_field = ObjectSqlField(self.table.adapter, self.pid_attr)

    def render_cell_content(self, session, record):
        args = (record[self.field.index], record[self.pid_field.index] or 0)
        return "%s (%i)" % args

class ConnectionGeneralStatSet(StatSet):
    def __init__(self, app, name, object):
        super(ConnectionGeneralStatSet, self).__init__(app, name, object)

        self.attrs = ("closing",)

class ConnectionIOStatSet(StatSet):
    def __init__(self, app, name, object):
        super(ConnectionIOStatSet, self).__init__(app, name, object)

        self.attrs = ("bytesFromClient", "bytesToClient",
                       "framesFromClient", "framesToClient")

class ConnectionOverview(Widget):
    def __init__(self, app, name, conn):
        super(ConnectionOverview, self).__init__(app, name)

        self.add_child(ConnectionIOStatSet(app, "io", conn))
        self.add_child(ConnectionGeneralStatSet(app, "general", conn))

        chart = self.SendReceiveRateChart(app, "sendrecv", conn)
        chart.stats = ("bytesFromClient", "bytesToClient")
        chart.mode = "rate"
        self.add_child(chart)

    def render_title(self, session):
        return "Overview"

    class SendReceiveRateChart(StatFlashChart):
        def render_title(self, session):
            return "Bytes sent and received"

class SessionFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.org_apache_qpid_broker.Session

        super(SessionFrame, self).__init__(app, name, cls)

        self.close = SessionClose(app, self)
        self.detach = SessionDetach(app, self)

class SessionClose(ObjectFrameTask):
    def get_title(self, session):
        return "Close"

    def do_invoke(self, invoc, sess):
        self.app.remote.qmf.close(sess, invoc.make_callback())

class SessionDetach(ObjectFrameTask):
    def get_title(self, session):
        return "Detach"

    def do_invoke(self, invoc, sess):
        self.app.remote.qmf.detach(sess, invoc.make_callback())

class SessionSelector(ObjectSelector):
    def __init__(self, app, name, conn):
        cls = app.model.org_apache_qpid_broker.Session

        super(SessionSelector, self).__init__(app, name, cls)

        self.conn = conn

        frame = "main.messaging.broker.connection.session"
        col = ObjectLinkColumn(app, "name", cls.name, cls._id, frame)
        self.add_column(col)
        self.add_search_filter(col)

        self.add_attribute_column(cls.attached)
        self.add_attribute_column(cls.detachedLifespan)
        self.add_attribute_column(cls.framesOutstanding)
        self.add_attribute_column(cls.clientCredit)

        self.close = SessionSelectionClose(app, self)
        self.detach = SessionSelectionDetach(app, self)

        self.enable_csv_export(conn)

class SessionSelectionClose(ObjectSelectorTask):
    def get_title(self, session):
        return "Close"

    def do_invoke(self, invoc, sess):
        self.app.remote.qmf.close(sess, invoc.make_callback())

class SessionSelectionDetach(ObjectSelectorTask):
    def get_title(self, session):
        return "Detach"

    def do_invoke(self, invoc, sess):
        self.app.remote.qmf.detach(sess, invoc.make_callback())
