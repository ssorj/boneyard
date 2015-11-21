from wooly import *
from wooly.forms import *
from wooly.resources import *
from wooly.widgets import *

from cumin.formats import *
from cumin.model import *
from cumin.objecttask import *
from cumin.parameters import *
from cumin.stat import *
from cumin.util import *
from cumin.widgets import *

from binding import *

import main

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.messaging.exchange")

class ExchangeFrame(ObjectFrame):
    def __init__(self, app, name, vhost):
        cls = app.model.org_apache_qpid_broker.Exchange

        super(ExchangeFrame, self).__init__(app, name, cls)

        self.icon_href = "resource?name=exchange-36.png"

        self.overview = ExchangeOverview(app, "overview", self.object)
        self.view.add_tab(self.overview)

        self.bindings = ExchangeBindingSelector(app, "ex_bindings", self.object)
        self.view.add_tab(self.bindings)

        self.remove = ExchangeRemove(app, self)
        self.add_binding = ExchangeBindingAdd(app, self)

class ExchangeRemove(ObjectFrameTask):
    def get_title(self, session):
        return "Remove"

    def do_exit(self, session):
        self.app.main_page.main.messaging.broker.view.show(session)

    def do_invoke(self, invoc, exchange):
        session = self.app.model.get_session_by_object(exchange)
        session.exchange_delete(exchange=exchange.name)
        session.sync()

        invoc.end()

class ExchangeBindingAdd(BindingAddTask):
    def __init__(self, app, frame):
        super(ExchangeBindingAdd, self).__init__(app, frame)

        self.form = ExchangeBindingAddForm(app, self.name, self)

class ExchangeBindingAddForm(BindingAddForm):
    def __init__(self, app, name, task):
        super(ExchangeBindingAddForm, self).__init__(app, name, task)

        self.x_field.input.disabled = True

class ExchangeSelector(ObjectSelector):
    def __init__(self, app, name, vhost):
        cls = app.model.org_apache_qpid_broker.Exchange

        super(ExchangeSelector, self).__init__(app, name, cls)

        self.vhost = vhost

        frame = "main.messaging.broker.exchange"
        col = self.ExchangeNameColumn(app, "name", cls.name, cls._id, frame)
        self.add_column(col)
        self.add_search_filter(col)

        self.add_attribute_column(cls.producerCount)
        self.add_attribute_column(cls.bindingCount)
        self.add_attribute_column(cls.msgRoutes)
        self.add_attribute_column(cls.byteRoutes)
    
        self.add_reference_filter(vhost, cls.vhostRef)

        self.remove = ExchangeSelectionRemove(app, self)

        self.enable_csv_export(vhost)

    class ExchangeNameColumn(ObjectLinkColumn):
        def render_cell_content(self, session, record):
            return record[self.field.index] or "Default exchange"

class ExchangeSelectionRemove(ObjectSelectorTask):
    def get_title(self, session):
        return "Remove"

    def get_item_content(self, session, item):
        return xml_escape(item.name) or "Default exchange"

    def do_invoke(self, invoc, exchange):
        session = self.app.model.get_session_by_object(exchange)
        session.exchange_delete(exchange=exchange.name)
        session.sync()

        invoc.end()

class ExchangeBindingSelector(BindingSelector):
    def __init__(self, app, name, exchange):
        super(ExchangeBindingSelector, self).__init__(app, name)

        self.exchange = exchange

        self.add_reference_filter(self.exchange, self.cls.exchangeRef)

        self.exchange_column.visible = False

        self.enable_csv_export(exchange)

class ExchangeTypeField(RadioItemSetField):
    def __init__(self, app, name):
        param = SymbolParameter(app, "param")
        param.default = "direct"

        super(ExchangeTypeField, self).__init__(app, name, param)

        self.add_parameter(param)

    def render_title(self, session):
        return "Routing"

    def do_get_items(self, session):
        items = list()

        item = RadioItem("direct")
        item.title = "Direct"
        item.description = "Route messages to queues by queue name"
        items.append(item)

        item = RadioItem("topic")
        item.title = "Topic"
        item.description = "Route messages to topics by matching routing-key pattern"
        items.append(item)

        item = RadioItem("fanout")
        item.title = "Fan out"
        item.description = \
            "Route messages to all queues bound to this exchange"
        items.append(item)

        item = RadioItem("header")
        item.title = "Header"
        item.description = \
            "Route messages to queues by the content of their headers"
        items.append(item)

        item = RadioItem("xml")
        item.title = "XML"
        item.description = "Route messages to queues by their XML content"
        items.append(item)

        return items

class ExchangeDurabilityField(RadioItemSetField):
    def __init__(self, app, name):
        param = BooleanParameter(app, "param")
        param.default = True

        super(ExchangeDurabilityField, self).__init__(app, name, param)

        # XXX don't like this
        self.add_parameter(param)

    def render_title(self, session):
        return "Durability"

    def do_get_items(self, session):
        items = list()

        item = RadioItem(True)
        item.title = "Durable"
        item.description = \
            "Save this exchange definition and restore it when the broker " + \
            "restarts"
        items.append(item)

        item = RadioItem(False)
        item.title = "Transient"
        item.description = \
            "Discard this exchange definition when the broker restarts"
        items.append(item)

        return items

class ExchangeArgumentsField(CheckboxItemSetField):
    def __init__(self, app, name):
        item_parameter = SymbolParameter(app, "item")

        super(ExchangeArgumentsField, self).__init__(app, name, item_parameter)

    def do_get_items(self, session):
        items = list()

        item = CheckboxItem("initial_value")
        item.title = "Initial value"
        item.description = "Save the last message encountered and send it to newly bound queues"
        items.append(item)

        item = CheckboxItem("message_sequence")
        item.title = "Sequence numbers"
        item.description = "Insert a sequence number into the header of each message"
        items.append(item)

        return items

    def render_title(self, session):
        return "Advanced options"

class ExchangeAdd(ObjectFrameTask):
    MSG_SEQUENCE = "qpid.msg_sequence"
    IVE = "qpid.ive"

    def __init__(self, app, frame):
        super(ExchangeAdd, self).__init__(app, frame)

        self.form = ExchangeAddForm(app, self.name, self)

    def get_title(self, session):
        return "Add exchange"

    def do_invoke(self, invoc, vhost, name, type, durable, sequence, ive):
        args = dict()

        if sequence:
            args[self.MSG_SEQUENCE] = 1

        if ive:
            args[self.IVE] = 1

        session = self.app.model.get_session_by_object(vhost)
        session.exchange_declare \
            (exchange=name, type=type, durable=durable, arguments=args)
        session.sync()

        invoc.end()

class ExchangeAddForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(ExchangeAddForm, self).__init__(app, name, task)

        self.exchange_name = ExchangeNameField(app, "exchange_name")
        self.main_fields.add_field(self.exchange_name)

        self.exchange_type = ExchangeTypeField(app, "exchange_type")
        self.main_fields.add_field(self.exchange_type)

        self.durability = ExchangeDurabilityField(app, "durability")
        self.main_fields.add_field(self.durability)

        self.args = ExchangeArgumentsField(app, "args")
        self.extra_fields.add_field(self.args)

    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            vhost = self.object.get(session)

            name = self.exchange_name.get(session)
            type = self.exchange_type.get(session)
            durable = self.durability.get(session)
            args = self.args.get(session)

            sequence_numbers = "sequence_numbers" in args
            initial_value = "initial_value" in args

            self.task.invoke(session, vhost, name, type,
                             durable, sequence_numbers, initial_value)
            self.task.exit_with_redirect(session)

class ExchangeGeneralStatSet(StatSet):
    def __init__(self, app, name, object):
        super(ExchangeGeneralStatSet, self).__init__(app, name, object)

        self.attrs = ("producerCount", "bindingCount")

class ExchangeIOStatSet(StatSet):
    def __init__(self, app, name, object):
        super(ExchangeIOStatSet, self).__init__(app, name, object)

        self.attrs = ("msgReceives", "msgRoutes",
                       "msgDrops", "byteReceives",
                       "byteRoutes", "byteDrops")

class ExchangeOverview(Widget):
    def __init__(self, app, name, exchange):
        super(ExchangeOverview, self).__init__(app, name)

        self.add_child(ExchangeIOStatSet(app, "io", exchange))
        self.add_child(ExchangeGeneralStatSet(app, "general", exchange))

        chart = self.ReceiveRouteDropRateChart(app, "recvroutedrop", exchange)
        chart.stats = ("msgReceives", "msgRoutes", "msgDrops")
        chart.mode = "rate"
        self.add_child(chart)

        chart = StatFlashChart(app, "producers", exchange)
        chart.stats = ("producerCount",)
        self.add_child(chart)

    def render_title(self, session):
        return "Overview"

    class ReceiveRouteDropRateChart(StatFlashChart):
        def render_title(self, session):
            return "Messages received, routed, and dropped"

class ExchangeInfo(object):
    @classmethod
    def is_builtin(cls, exchange):
        return exchange.name in ExchangeInfo.get_builtins()

    @classmethod
    def get_builtins(cls):
        return ["", "amq.direct", "amq.topic", "amq.match",
                "amq.fanout", "qpid.management"]
