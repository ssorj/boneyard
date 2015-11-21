import logging

from mint import *
from wooly import *
from cumin.objectframe import *
from cumin.objectselector import *
from cumin.objecttask import *
from wooly.widgets import *
from cumin.widgets import *
from cumin.parameters import *
from cumin.formats import *
from cumin.util import *

from queue import *
from exchange import *

import main

strings = StringCatalog(__file__)

class BrokerLinkFrame(ObjectFrame):
    def __init__(self, app, name, broker):
        cls = app.model.org_apache_qpid_broker.Link

        super(BrokerLinkFrame, self).__init__(app, name, cls)

        self.view.add_tab(RouteSelector(app, "routes", self.object))

        self.route_add = RouteAdd(app, self)
        self.remove = BrokerLinkRemove(app, self)

    def get_title(self, session):
        obj = self.object.get(session)

        return "%s '%s'" % (obj._class._title, obj.host)

class BrokerLinkRemoveForm(ObjectFrameTaskForm):
    def render_content(self, session):
        obj = self.object.get(session)
        return xml_escape(obj.host)

class BrokerLinkRemove(ObjectFrameTask):
    def __init__(self, app, frame):
        super(BrokerLinkRemove, self).__init__(app, frame)

        self.form = BrokerLinkRemoveForm(app, self.name, self)

    def get_title(self, session):
        return "Remove broker link"

    def do_exit(self, session):
        self.app.main_page.main.messaging.broker.view.show(session)

    def do_invoke(self, invoc, link):
        self.app.remote.qmf.close(link, invoc.make_callback())

class BrokerLinkSelector(ObjectSelector):
    def __init__(self, app, name, vhost):
        cls = app.model.org_apache_qpid_broker.Link

        super(BrokerLinkSelector, self).__init__(app, name, cls)

        self.vhost = vhost

        self.add_reference_filter(self.vhost, cls.vhostRef)

        frame = "main.messaging.broker.link"
        col = ObjectLinkColumn(app, "name", cls.host, cls._id, frame)
        self.add_column(col)
        self.add_search_filter(col)

        self.add_attribute_column(cls.port)
        self.add_attribute_column(cls.state)
        self.add_attribute_column(cls.transport)
        self.add_attribute_column(cls.durable)

        self.remove = BrokerLinkSelectionRemove(app, self)

        self.enable_csv_export(vhost)

class BrokerLinkSelectionRemove(ObjectSelectorTask):
    def get_title(self, session):
        return "Remove broker link"

    def do_invoke(self, invoc, link):
        self.app.remote.qmf.close(link, invoc.make_callback())

class RouteSelector(ObjectSelector):
    def __init__(self, app, name, link):
        cls = app.model.org_apache_qpid_broker.Bridge

        super(RouteSelector, self).__init__(app, name, cls)

        self.link = link

        self.add_reference_filter(self.link, cls.linkRef)

        col = self.add_attribute_column(cls.src)
        self.add_search_filter(col)

        self.add_attribute_column(cls.dest)
        self.add_attribute_column(cls.key)
        self.add_attribute_column(cls.tag)
        self.add_attribute_column(cls.excludes)

        self.remove = RouteSelectionRemove(app, self)

class RouteSelectionRemove(ObjectSelectorTask):
    def get_title(self, session):
        return "Remove"

    def do_invoke(self, invoc, route):
        self.app.remote.qmf.close(route, invoc.make_callback())

# XXX RouteFrame

class RouteRemove(ObjectFrameTask):
    def get_title(self, session):
        return "Remove"

    def do_exit(self, session):
        self.app.main_page.main.messaging.broker.view.show(session)

    def do_invoke(self, invoc, route):
        self.app.remote.qmf.close(route, invoc.make_callback())

class LinkGeneralStatSet(StatSet):
    def __init__(self, app, name, object):
        super(LinkGeneralStatSet, self).__init__(app, name, object)

        self.attrs = ("closing",)

class LinkIOStatSet(StatSet):
    def __init__(self, app, name, object):
        super(LinkIOStatSet, self).__init__(app, name, object)

        self.attrs = ("framesFromPeer", "framesToPeer",
                       "bytesFromPeer", "bytesToPeer")

class LinkStats(TabbedModeSet):
    def __init__(self, app, name, link):
        super(LinkStats, self).__init__(app, name)

        self.add_child(LinkIOStatSet(app, "io", link))
        self.add_child(LinkGeneralStatSet(app, "general", link))

        chart = self.ReceiveRouteDropRateChart(app, "recvroutedrop", link)
        chart.stats = ("msgReceives", "msgRoutes", "msgDrops")
        chart.mode = "rate"
        self.add_child(chart)

        chart = StatFlashChart(app, "producers")
        chart.stats = ("producerCount",)
        self.add_child(chart)

    def render_title(self, session):
        return "Statistics"

    class ReceiveRouteDropRateChart(StatFlashChart):
        def render_title(self, session):
            return "Messages received, routed, and dropped"

class ExchangeInputSet(RadioInputSet):
    def __init__(self, app, name, state):
        super(ExchangeInputSet, self).__init__(app, name, None)

        self.param = IntegerParameter(app, "param")
        self.add_parameter(self.param)

        self.state = state

    def do_get_items(self, session, *args):
        exchanges = list()

        link = self.form.link.get(session)
        if link is not None:
            vhost = link.vhost
            sortedExchanges = sorted_by(vhost.exchanges)

            for exchange in sortedExchanges:
                if ExchangeInfo.is_builtin(exchange) or \
                   (not exchange._get_qmfDeleteTime() and \
                    not (self.state.is_active(session) and not is_active(exchange))):
                    if not exchange.name in ["qpid.management", ""]:
                        if not self.param.get(session):
                            self.param.set(session, exchange.id)
                        exchanges.append(exchange)

        return exchanges

    def render_item_value(self, session, exchange):
        return exchange.id

    def render_item_content(self, session, exchange):
        return xml_escape(exchange.name)

    def render_item_checked_attr(self, session, exchange):
        if self.param.get(session) == exchange.id:
            return "checked=\"checked\""

class ExchangeRadioField(FormField):
    def __init__(self, app, name):
        super(ExchangeRadioField, self).__init__(app, name)

        self.state = ExchangeState(app, "phase")
        self.add_child(self.state)

        self.__exchanges = ExchangeInputSet(app, "inputs", self.state)
        self.add_child(self.__exchanges)

    def get(self, session):
        return self.__exchanges.get(session)

    def render_title(self, session):
        return "Choose an Exchange"
    
    def render_field_help(self, session):
        return ""
    
    def render_errors(self, session):
        return ""

class RouteAdd(ObjectFrameTask):
    def __init__(self, app, frame):
        super(RouteAdd, self).__init__(app, frame)

        self.form = RouteAddForm(app, self.name, self)

    def get_title(self, session):
        return "Add route"

    def do_invoke(self, invoc, link, exchange, key, tag, dynamic, sync,
                  excludes):

        self.app.remote.qmf.bridge(link, link.durable, exchange.name, exchange.name,
                               key, tag, excludes, False, False, dynamic, sync, 
                               invoc.make_callback())

class RouteAddForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(RouteAddForm, self).__init__(app, name, task)

        self.link = LinkParameter(app, "link")
        self.add_parameter(self.link)

        self.exchange = ExchangeRadioField(app, "exchange")
        self.add_field(self.exchange)

        self.key = TextField(app, "key")
        self.key.set_title("Routing Key")
        self.add_field(self.key)

        self.more = MoreFieldSet(app, "more")
        self.add_field(self.more)

        self.help = self.BridgeAddHelpField(app, "help")
        self.more.add_field(self.help)

        self.tag = TextField(app, "tag")
        self.tag.required = False
        self.tag.set_title("Tag")
        self.more.add_field(self.tag)

        self.excludes = TextField(app, "excludes")
        self.excludes.required = False
        self.excludes.set_title("Excludes")
        self.more.add_field(self.excludes)

        self.dynamic = self.DynamicField(app, "dynamic")
        self.more.add_field(self.dynamic)

        self.sync = self.SyncField(app, "sync")
        self.more.add_field(self.sync)

    def process_display(self, session):
        link = self.link.get(session)

        if not self.tag.get(session):
            brokerId = QpidAgentId.fromString(link.qmfAgentId).brokerId
            self.tag.set(session, brokerId)

        if not self.excludes.get(session):
            self.excludes.set(session, "%s:%s" % (link.host, link.port))

        if not self.sync.get(session):
            self.sync.set(session, self.sync.get_default(session))

    class SyncField(IntegerField):
        def render_title(self, session):
            return "Ack"

        def render_field_help(self, session):
             return "Acknowledge transfers over the bridge in batches of N"

        def get_default(self, session):
            return 0

    class DynamicField(TwoOptionRadioField):
        def render_title(self, session):
            return "Dynamic Route?"

        def render_field_help(self, session):
            return "(Should the added route be dynamic)"

        def render_title_1(self, session):
            return "Dynamic"

        def render_title_2(self, session):
            return "Not dynamic"

    class BridgeAddHelpField(FormField):
        pass

    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            link = self.link.get(session)

            key = self.key.get(session)
            tag = self.tag.get(session)
            excludes = self.excludes.get(session)
            exchange_id = self.exchange.get(session)
            exchange = Exchange.get(int(exchange_id))
            durable = link.durable
            dynamic = self.dynamic.get(session) == "yes"
            sync = self.sync.get(session)

            self.task.invoke(session, link, exchange, key, tag,
                             dynamic, sync, excludes)
            self.task.exit_with_redirect(session)

class RouteSetRemoveForm(CuminTaskForm):
    def __init__(self, app, name, task):
        super(RouteSetRemoveForm, self).__init__(app, name, task)

        item = RouteParameter(app, "item")

        self.object = ListParameter(app, "route", item)
        self.add_parameter(self.object)

class BrokerLinkAdd(ObjectFrameTask):
    def __init__(self, app, frame):
        super(BrokerLinkAdd, self).__init__(app, frame)

        self.form = BrokerLinkAddForm(app, self.name, self)

    def get_title(self, session):
        return "Add broker link"

    def do_invoke(self, invoc, vhost, host, port, durable, username,
                  password, transport):
        cursor = self.app.database.get_read_cursor()

        cls = self.app.model.org_apache_qpid_broker.Broker
        obj = cls.get_object(cursor, _id=vhost._brokerRef_id)

        if username == "anonymous":
            mech = "ANONYMOUS"
        else:
            mech = "PLAIN"

        self.app.remote.qmf.connect(obj, host, port, durable, mech, username,
                                password, transport, invoc.make_callback())

class BrokerLinkAddForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(BrokerLinkAddForm, self).__init__(app, name, task)

        self.host = self.Host(app, "host")
        self.add_field(self.host)

        self.port = self.PortField(app, "port")
        self.add_extra_field(self.port)

        self.username = self.UsernameField(app, "username")
        self.add_extra_field(self.username)

        self.password = self.PassField(app, "password")
        self.add_extra_field(self.password)

        self.durable = self.DurableField(app, "durable")
        self.add_extra_field(self.durable)

        self.transport = self.TransportField(app, "transport")
        self.add_extra_field(self.transport)

    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            vhost = self.object.get(session)

            host = self.host.get(session)
            port = self.port.get(session) or 5672
            username = self.username.get(session) or "anonymous"
            password = self.password.get(session)
            durable = self.durable.get(session) == "yes"
            transport = self.transport.get(session)

            # XXX PortField should enforce this

            if port:
                port = int(port)

            self.task.invoke(session, vhost, host, port,
                             durable, username, password, transport)
            self.task.exit_with_redirect(session)

    class Host(NameField):
        def render_title(self, session):
            return "Address"

    class PortField(IntegerField):
        def __init__(self, app, name):
            super(BrokerLinkAddForm.PortField, self).__init__(app, name)

            self.input.size = 5
            self.css_class = "compact first"

        def render_title(self, session):
            return "Port"

    class UsernameField(StringField):
        def render_title(self, session):
            return "Username"

        def render_form_field_class(self, session):
            return "compact"

    class PassField(PasswordField):
        def render_title(self, session):
            return "Password"

        def render_form_field_class(self, session):
            return "compact last"

    class TransportField(RadioField):
        def __init__(self, app, name):
            super(BrokerLinkAddForm.TransportField, self).__init__ \
                (app, name, None)

            self.param = Parameter(app, "param")
            self.param.default = "tcp"
            self.add_parameter(self.param)

            option = self.TCP(app, "tcp", self.param)
            self.add_option(option)

            option = self.SSL(app, "ssl", self.param)
            self.add_option(option)

            option = self.RDMA(app, "rdma", self.param)
            self.add_option(option)

        def render_title(self, session):
            return "Transport-type"

        def render_field_help(self, session):
            return "(Transport to use)"

        class TCP(RadioFieldOption):
            def render_title(self, session):
                return "tcp"

        class SSL(RadioFieldOption):
            def render_title(self, session):
                return "ssl"

        class RDMA(RadioFieldOption):
            def render_title(self, session):
                return "rdma"

    class DurableField(TwoOptionRadioField):
        def render_title(self, session):
            return "Restore if broker restarts?"

        def render_field_help(self, session):
            return "(Should the added configuration be durable)"

        def render_title_1(self, session):
            return "Yes, restore if broker restarts"

        def render_title_2(self, session):
            return "No, do not restore if broker restarts"
