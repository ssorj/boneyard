import logging

from rosemary.model import RosemaryObject

from cumin.formats import fmt_shorten
from cumin.objectframe import ObjectFrameTaskForm, ObjectFrame, ObjectFrameTask
from cumin.objectselector import ObjectSelectorTask, ObjectSelector,\
    ObjectLinkColumn
from cumin.widgets import SubmitSwitch, QueueBindingField, ExchangeBindingField
from cumin.sqladapter import ObjectSqlAdapter

from wooly import Widget, Parameter
from wooly.template import WidgetTemplate
from wooly.forms import Form, FormField, FormError, MissingValueError,\
    StringField
from wooly.parameters import DictParameter, StringParameter, ListParameter,\
    IntegerParameter
from wooly.util import StringCatalog, Writer
from cumin.util import xml_escape

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.messaging.exchange")

class BindingSelectionRemove(ObjectSelectorTask):
    def get_title(self, session):
        return "Remove"

    def do_invoke(self, invoc, binding):
        assert isinstance(binding, RosemaryObject)

        cursor = self.app.database.get_read_cursor()

        queue = None
        exchange = None

        try:
            cls = self.app.model.org_apache_qpid_broker.Queue
            queue = cls.get_object_by_id(cursor, binding._queueRef_id)
            cls = self.app.model.org_apache_qpid_broker.Exchange
            exchange = cls.get_object_by_id(cursor, binding._exchangeRef_id)
        except Exception, e:
            invoc.status = "failed"
            invoc.exception = e
            log.debug("Binding removal failed", exc_info=True)

        if queue and exchange:
            session = self.app.model.get_session_by_object(binding)
            session.exchange_unbind(queue=queue.name,
                                    exchange=exchange.name,
                                    binding_key=binding.bindingKey)
            session.sync()

        invoc.end()

class BindingFrame(ObjectFrame):
    def __init__(self, app, name, vhost):
        cls = app.model.org_apache_qpid_broker.Binding

        super(BindingFrame, self).__init__(app, name, cls)

        self.remove = BindingRemove(app, self)
    
class BindingAdd(ObjectFrameTask):
    def __init__(self, app, frame):
        super(BindingAdd, self).__init__(app, frame)

        self.form = BindingAddForm(app, self.name, self)

    def get_title(self, session):
        return "Add binding"

    def do_invoke(self, invoc, vhost, queue, exchange, binding_key, args):
        session = self.app.model.get_session_by_object(vhost)
        session.exchange_bind(queue=queue.name, exchange=exchange.name,
                              binding_key=binding_key, arguments=args)
        session.sync()

        invoc.end()

class BindingRemoveForm(ObjectFrameTaskForm):
    def render_content(self, session):
        # binding doesn't have a name, use the binding key
        obj = self.object.get(session)
        return xml_escape(obj.bindingKey)

class BindingRemove(ObjectFrameTask):
    def __init__(self, app, frame):
        super(BindingRemove, self).__init__(app, frame)

        self.form = BindingRemoveForm(app, self.name, self)

    def get_title(self, session):
        return "Remove"

    def do_exit(self, session):
        self.app.main_page.main.messaging.broker.view.show(session)

    def do_invoke(self, invoc, binding):
        assert isinstance(binding, RosemaryObject)

        cursor = self.app.database.get_read_cursor()

        queue = None
        exchange = None

        try:
            cls = self.app.model.org_apache_qpid_broker.Queue
            queue = cls.get_object_by_id(cursor, binding._queueRef_id)
            cls = self.app.model.org_apache_qpid_broker.Exchange
            exchange = cls.get_object_by_id(cursor, binding._exchangeRef_id)
        except Exception, e:
            invoc.status = "failed"
            invoc.exception = e
            log.debug("Binding removal failed", exc_info=True)

        if queue and exchange:
            session = self.app.model.get_session_by_object(binding)
            session.exchange_unbind(queue=queue.name,
                                    exchange=exchange.name,
                                    binding_key=binding.bindingKey)
            session.sync()

        invoc.end()

class BindingData(ObjectSqlAdapter):
    def __init__(self, app):
        binding = app.model.org_apache_qpid_broker.Binding
        exchange = app.model.org_apache_qpid_broker.Exchange
        queue = app.model.org_apache_qpid_broker.Queue

        super(BindingData, self).__init__(app, binding)

        self.add_join(exchange, binding.exchangeRef, exchange._id)
        self.add_join(queue, binding.queueRef, queue._id)

    def get_data(self, values, options):
        return super(BindingData, self).get_data(values, options)

class BindingSelector(ObjectSelector):
    def __init__(self, app, name):
        binding = app.model.org_apache_qpid_broker.Binding
        exchange = app.model.org_apache_qpid_broker.Exchange
        queue = app.model.org_apache_qpid_broker.Queue

        super(BindingSelector, self).__init__(app, name, binding)

        self.table.adapter = BindingData(app)

        frame = "main.messaging.broker.binding"
        col = ObjectLinkColumn \
            (app, "binding", binding.bindingKey, binding._id, frame)
        self.add_column(col)
        self.add_search_filter(col)

        frame = "main.messaging.broker.exchange"
        self.exchange_column = self.Exchange \
            (app, "exchange", exchange.name, exchange._id, frame)
        self.add_column(self.exchange_column)

        frame = "main.messaging.broker.queue"
        self.queue_column = self.Queue \
            (app, "queue", queue.name, queue._id, frame)
        self.add_column(self.queue_column)

        self.add_attribute_column(binding.origin)
        self.add_attribute_column(binding.msgMatched)
 
        self.remove = BindingSelectionRemove(app, self)

    class Exchange(ObjectLinkColumn):
        def render_header_content(self, session):
            return "Exchange"

        def render_cell_content(self, session, record):
            return record[self.field.index] or "Default exchange"

    class Queue(ObjectLinkColumn):
        def render_header_content(self, session):
            return "Queue"

class ExchangeInput(Widget):
    def __init__(self, app, name):
        super(ExchangeInput, self).__init__(app, name)

        self.exchange = None
        self.instance_data = None

        self.name_tmpl = WidgetTemplate(self, "name_html")
        self.key_tmpl = WidgetTemplate(self, "key_html")

        self.form = None

    def init(self):
        super(ExchangeInput, self).init()

        for anc in self.ancestors:
            if isinstance(anc, Form):
                self.form = anc

    def get_exchange_info(self, session, exchange):
        binding_info = self.form.bindings.dict_param.get(session)
        if str(exchange._id) in binding_info:
            return binding_info[str(exchange.id)]

    def get_exchange_info_for(self, session, exchange, key):
        exchange_info = self.get_exchange_info(session, exchange)
        if exchange_info:
            if key in exchange_info:
                return exchange_info[key]

    def render_exchange_name(self, session, exchange):
        return exchange.name

    def render_exchange_fmt_name(self, session, exchange):
        return fmt_shorten(exchange.name)

    def render_name_path(self, session, *args):
        return DictParameter.sep().join((self.instance_data, "name"))

    def render_exchange_type(self, session, exchange):
        return exchange.type

    def render_exchange_type_path(self, session, exchange):
        return DictParameter.sep().join((self.instance_data, "type"))

    def render_exchange_id(self, session, exchange):
        return exchange._id

    def render_exchange_checked(self, session, exchange):
        exchange_info = self.get_exchange_info(session, exchange)
        if exchange_info:
            if "name" in exchange_info:
                return "checked=\"checked\""

    def render_exchange_name_input(self, session, exchange):
        writer = Writer()
        self.name_tmpl.render(writer, session, exchange)
        return writer.to_string()

    def render_exchange_key_input(self, session, exchange):
        writer = Writer()
        self.key_tmpl.render(writer, session, exchange)
        return writer.to_string()

    def render_onclick(self, session, exchange):
        pass

    def render_list_error(self, session, exchange):
        errors = self.parent.binding_errors.get(session)
        if exchange.name in errors:
            return "<ul class=\"errors\" style=\"margin:0; float:left;\"><li>%s</li></ul>" % \
                "</li><li>".join(errors[exchange.name])

    def render_dict_error(self, session, exchange, key):
        errors = self.parent.binding_errors.get(session)
        if exchange.name in errors:
            exchange_errors = errors[exchange.name]
            if key in exchange_errors:
                return "<ul class=\"errors\" style=\"margin:0; float:left;\"><li>%s</li></ul>" % \
                "</li><li>".join(exchange_errors[key])

    def set_instance_data(self, exchange, dict_key):
        self.exchange = exchange
        self.instance_data = dict_key

class FanoutExchangeInput(ExchangeInput):
    pass

class BindingKeyExchangeInput(ExchangeInput):
    def __init__(self, app, name):
        super(BindingKeyExchangeInput, self).__init__(app, name)

    def render_key_path(self, session, exchange):
        return DictParameter.sep().join((self.instance_data, "key"))

    def render_key_error(self, session, exchange):
        return self.render_list_error(session, exchange)

    def render_key_value(self, session, exchange):
        return self.get_exchange_info_for(session, exchange, "key")

class DirectExchangeInput(BindingKeyExchangeInput):
    pass

class TopicExchangeInput(BindingKeyExchangeInput):
    pass

class XMLExchangeInput(BindingKeyExchangeInput):
    def __init__(self, app, name):
        super(XMLExchangeInput, self).__init__(app, name)

    def render_xquery_path(self, session, exchange):
        return DictParameter.sep().join((self.instance_data, "xquery"))

    def render_headers_class(self, session, exchange):
        exchange_info = self.get_exchange_info(session, exchange)
        if not exchange_info or not "name" in exchange_info:
            return "initial_header_state"

    def render_key_error(self, session, exchange):
        return self.render_dict_error(session, exchange, "key")

    def render_onclick(self, session, exchange):
        return "onclick=\"toggle_row(this, 'xml_extra.%s')\"" % str(exchange.id)

    def render_xml_extra(self, session, exchange):
        return "xml_extra.%s" % str(exchange.id)

    def render_xquery_error(self, session, exchange):
        return self.render_dict_error(session, exchange, "xquery")

    def render_xquery_value(self, session, exchange):
        return self.get_exchange_info_for(session, exchange, "xquery")

    def process_input(self, this_exchange, arguments):
        if "xquery" in this_exchange:
            arguments["xquery"] = this_exchange["xquery"]

class HeadersExchangeInput(BindingKeyExchangeInput):
    def __init__(self, app, name):
        super(HeadersExchangeInput, self).__init__(app, name)

    def render_x_match_path(self, session, exchange):
        return DictParameter.sep().join((self.instance_data, "x-match"))

    def render_mkey_path(self, session, exchange):
        return DictParameter.sep().join((self.instance_data, "mkey"))

    def render_headers_class(self, session, exchange):
        exchange_info = self.get_exchange_info(session, exchange)
        if not exchange_info or not "name" in exchange_info:
            return "initial_header_state"

    def render_all_checked(self, session, exchange):
        checked = self.render_any_checked(session, exchange)
        if not checked:
            return "checked=\"checked\""

    def render_any_checked(self, session, exchange):
        exchange_info = self.get_exchange_info(session, exchange)
        if exchange_info:
            if "x-match" in exchange_info:
                if exchange_info["x-match"] == "any":
                    return "checked=\"checked\""

    def render_mkey1_value(self, session, exchange):
        return self.get_exchange_info_for(session, exchange, "mkey.1")

    def render_mkey2_value(self, session, exchange):
        return self.get_exchange_info_for(session, exchange, "mkey.2")

    def render_mkey3_value(self, session, exchange):
        return self.get_exchange_info_for(session, exchange, "mkey.3")

    def render_mnv1_value(self, session, exchange):
        return self.get_exchange_info_for(session, exchange, "mkey.1.nv")

    def render_mnv2_value(self, session, exchange):
        return self.get_exchange_info_for(session, exchange, "mkey.2.nv")

    def render_mnv3_value(self, session, exchange):
        return self.get_exchange_info_for(session, exchange, "mkey.3.nv")

    def render_key_error(self, session, exchange):
        return self.render_dict_error(session, exchange, "key")

    def render_mkey1_error(self, session, exchange):
        return self.render_dict_error(session, exchange, "mkey.1")

    def render_mkey2_error(self, session, exchange):
        return self.render_dict_error(session, exchange, "mkey.2")

    def render_mkey3_error(self, session, exchange):
        return self.render_dict_error(session, exchange, "mkey.3")

    def render_onclick(self, session, exchange):
        return "onclick=\"toggle_row(this, 'headers_extra.%s')\"" % \
            str(exchange._id)

    def render_headers_extra(self, session, exchange):
        return "headers_extra.%s" % str(exchange._id)

    def process_input(self, this_exchange, arguments):
        # x-match is a radio button, it must have a value
        arguments["x-match"] = this_exchange["x-match"]
        # Fill out the other arguments.
        # The form has input boxes named mkey.* and mkey.*.nv
        # We need to create an arguments dictionary entry
        # of the form {mkey.*.value: mkey.*.nv.value}
        for match_info in this_exchange:
            if this_exchange[match_info]:
                if match_info.startswith("mkey") \
                    and not match_info.endswith("nv"):
                    # find the value in the matching .nv field
                    match_value = self._find_match_value(this_exchange, match_info)
                    # it is valid for the value in the .nv field
                    # to be empty
                    arguments[this_exchange[match_info]] = \
                        match_value or None

    def _find_match_value(self, this_exchange, match_info):
        for m_info in this_exchange:
            if m_info.startswith(match_info):
                if m_info.endswith("nv"):
                    return this_exchange[m_info]

class ExchangeState(SubmitSwitch):
    def __init__(self, app, name):
        super(ExchangeState, self).__init__(app, name)

        self.add_state("c", "Active", bm="phase")
        self.add_state("a", "All", bm="phase")

    def is_all(self, session):
        return self.get(session) == "a"

    def is_active(self, session):
        return self.get(session) == "c"

class ExchangeKeysField(FormField):
    def __init__(self, app, name, exchange):
        super(ExchangeKeysField, self).__init__(app, name)

        self.title = "Initial bindings"
        self.exchange = exchange

        name = StringParameter(app, "name")
        self.names = ListParameter(app, "names", name)
        self.add_parameter(self.names)

        value = StringParameter(app, "value")
        self.values = ListParameter(app, "values", value)
        self.add_parameter(self.values)

        self.count = IntegerParameter(app, "count")
        self.count.default = 3
        self.add_parameter(self.count)

        self.inputs_container_tmpl = WidgetTemplate(self, "input_container_html")
        self.inputs_tmpl = WidgetTemplate(self, "inputs_html")

    def init(self):
        """ we added parameters directly to the FormField instead
            of adding FormInputs. XXX should this logic be moved up to FormField? """
        super(ExchangeKeysField, self).init()
        for param in self.parameters:
            self.form.form_params.add(param)

    def render_title(self, session):
        return self.title

    def render_input_fields(self, session, *args):
        count = self.count.get(session)
        writer = Writer()
        for i in range(count):
            self.inputs_tmpl.render(writer, session, i)
        return writer.to_string()

    def render_inputs(self, session, *args):
        writer = Writer()
        self.inputs_container_tmpl.render(writer, session, *args)
        return writer.to_string()

    def render_n_name(self, session, i):
        return self.names.path

    def render_v_name(self, session, i):
        return self.values.path

    def render_n_value(self, session, i):
        names = self.names.get(session)
        return len(names) > i and xml_escape(names[i]) or ""

    def render_v_value(self, session, i):
        values = self.values.get(session)
        return len(values) > i and xml_escape(values[i]) or ""

    def get_exchange(self, session):
        exchange_string = self.exchange.get(session)
        if exchange_string:
            if exchange_string == "Default exchange":
                exchange_string = ""
            obj = self.form.object.get(session)
            cls = self.app.model.org_apache_qpid_broker.Exchange
            vhostid = obj._class._name == "Vhost" and obj._id or obj._vhostRef_id
            exchanges = cls.get_selection(session.cursor, name=exchange_string, _vhostRef_id=vhostid)
            if len(exchanges):
                return exchanges[0]
        return None

    def get(self, session):
        ret_dict = dict()
        exchange = self.get_exchange(session)
        if exchange:
            if exchange.type == "headers" or exchange.type == "xml":
                names = self.names.get(session)
                values = self.values.get(session)

                for name, value in zip(names, values):
                    if name:
                        ret_dict[name] = value
        return ret_dict

    def validate(self, session):
        exchange = self.get_exchange(session)
        names = self.names.get(session)
        values = self.values.get(session)

        if exchange:
            if exchange.type == "headers":
                if not "x-match" in names:
                    error = FormError("x-match argument is required for this exchange")
                    self.form.errors.add(session, error)

                for i in range(len(names)):
                    if names[i]:
                        if names[i] == "x-match":
                            if not values[i] == "all" and not values[i] == "any":
                                error = FormError("Argument name x-match must have a value of <i>all</i> or <i>any</i>")
                                self.form.errors.add(session, error)
                        else:
                            if not values[i]:
                                error = FormError("Missing argument value for name: %s" % names[i])
                                self.form.errors.add(session, error)

                for i in range(len(values)):
                    if values[i]:
                        if not names[i]:
                            error = FormError("Missing argument name for value: %s" % values[i])
                            self.form.errors.add(session, error)

            elif exchange.type == "xml":
                if not "xquery" in names:
                    error = FormError("xquery argument is required for this exchange")
                    self.form.errors.add(session, error)

class BindingAddForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(BindingAddForm, self).__init__(app, name, task)

        self.queue = Parameter(app, "queue")
        self.add_parameter(self.queue)
        self.q_field = QueueBindingField(app, "q_field", self.queue)
        self.add_field(self.q_field)

        self.exchange = Parameter(app, "exchange")
        self.add_parameter(self.exchange)
        self.x_field = ExchangeBindingField(app, "x_field", self.exchange)
        self.add_field(self.x_field)

        self.key = self.KeyField(app, "key")
        self.add_field(self.key)

        self.bindings = self.ExchangeBindings(app, "bindings", self.exchange)
        self.add_field(self.bindings)

    def init(self):
        super(BindingAddForm, self).init()
        self.form_params.add(self.queue)
        self.form_params.add(self.exchange)

    def render_title(self, session):
        return self.task.get_description(session)

    def render_key_id(self, session):
        return self.key.path

    def validate(self, session):
        super(BindingAddForm, self).validate(session)

        queue = self.queue.get(session)
        exchange = self.bindings.get_exchange(session)
        key = self.key.get(session)

        if not queue:
            error = FormError("A valid queue name is required")
            self.errors.add(session, error)
        if not exchange:
            error = FormError("A valid exchange name is required")
            self.errors.add(session, error)
        else:
            if not exchange.type == "fanout":
                if not key:
                    error = MissingValueError(self.key)
                    self.errors.add(session, error)

    def process_submit(self, session):
        self.validate(session)
        if not self.errors.get(session):
            queue = self.queue.get(session)
            exchange = self.exchange.get(session)
            if exchange == "Default exchange":
                exchange = ""
            key = self.key.get(session)
            arguments = self.bindings.get(session)
            obj = self.object.get(session)

            self.task.invoke(session, obj, queue, exchange, key, arguments)
            self.task.exit_with_redirect(session)

    class KeyField(StringField):
        def render_row_id(self, session):
            return "id='%s'" % self.path

        def render_title(self, session):
            return "Binding Key"

    class ExchangeBindings(ExchangeKeysField):
        def render_id(self, session, *args):
            cls = "ExchangeHiddenRow"
            exchange = self.get_exchange(session)
            if exchange and exchange.type == 'headers':
                cls = ""
            return cls and "%s\" class=\"%s" % (self.path, cls) or self.path

        def render_title(self, session):
            return "Arguments"
