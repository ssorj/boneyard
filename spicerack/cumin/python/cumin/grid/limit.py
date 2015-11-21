from cumin.formats import fmt_link
from cumin.objectframe import ObjectFrame, ObjectFrameTask, \
    ObjectFrameTaskForm
from cumin.objectselector import ObjectTableColumn, ObjectQmfSelector, \
    ObjectQmfTable
from cumin.qmfadapter import ObjectQmfAdapter
from wooly.forms import StringField, StringInput, IntegerField, RealField, \
    FormButton, FormField, FormError, CheckboxInput
from wooly.util import StringCatalog
from wooly.widgets import TabbedModeSet
from wooly.parameters import *
import logging

from sage.util import call_async


strings = StringCatalog(__file__)
log = logging.getLogger("cumin.limit")
LIMIT_FLOAT_VALUE_FOR_UNLIMITED = 1000000.0

class LimitAdapter(ObjectQmfAdapter):
    def get_negotiator(self, session):
        cls = self.app.model.com_redhat_grid.Negotiator
        negotiator = self.app.model.find_youngest(cls, session.cursor)
        return negotiator

    def get_count(self, values):
        data = self.do_get_data(values)
        return len(data)

    def get_qmf_results(self, values):
        # used to get the cached limits, and to determine
        # if there was an exception while getting the data

        session = values['session']
        negotiator = self.get_negotiator(session)

        return self.app.model.get_negotiator_limits(negotiator)

    def do_get_data(self, values):
        results = self.get_qmf_results(values)
        limits = results.data

        if limits is None or len(limits) == 0:
            return {}

        return limits

    def process_record(self, key, record):
        return [key, record["CURRENT"], record["MAX"]]

class LimitTable(ObjectQmfTable):
    def __init__(self, app, name, cls):
        super(LimitTable, self).__init__(app, name, cls)

        self.name_col = self.NameColumn(app, "name", cls.Name)
        self.add_column(self.name_col)

        col = self.UsageColumn(app, "curr", cls.Usage)
        self.add_column(col)

        col = self.MaxColumn(app, "max", cls.Allowance)
        self.add_column(col)

    class NameColumn(ObjectTableColumn):
        def render_cell_content(self, session, data):
            limit_name = super(LimitTable.NameColumn, self).render_cell_content(session, data)
            if session.page == self.app.export_page:
                return limit_name

            limit_max = data[2]
            negotiator = self.parent.adapter.get_negotiator(session)
            self.frame.limit.id.set(session, negotiator._id)
            self.frame.limit.set_limit.form.limit_name.set(session, limit_name)
            self.frame.limit.set_limit.form.limit_max.set(session, limit_max)
            return limit_name

    class UsageColumn(ObjectTableColumn):
        def render_text_align(self, session):
            return "right"

    class MaxColumn(ObjectTableColumn):
        def __init__(self, app, name, attr):
            super(LimitTable.MaxColumn, self).__init__(app, name, attr)
            self.do_escape = False
               
        def render_text_align(self, session):
            return "right"

        def render_cell_content(self, session, data):
            value = None
            limit_max = super(LimitTable.MaxColumn, self).render_cell_content(session, data)
            try:
                limit_max = float(limit_max)
                if limit_max >= LIMIT_FLOAT_VALUE_FOR_UNLIMITED:
                    limit_max = "Unlimited"
            except:
                limit_max = 0
                
            # if we are exporting csv, we don't want to return a link, so we check here
            if session.page == self.app.export_page:
                value = limit_max
            else:
                href = self.frame.limit.set_limit.get_href(session)
                value = fmt_link(href, limit_max)
            
            return value

class LimitSelector(ObjectQmfSelector):
    def __init__(self, app, name):
        cls = app.model.com_redhat_cumin_grid.Limit

        super(LimitSelector, self).__init__(app, name, cls)

        self.add_search_filter(self.table.name_col)
        self.table.adapter = LimitAdapter(app, cls)

        self.enable_csv_export()

    def create_table(self, app, name, cls):
        return LimitTable(app, name, cls)

    def render_title(self, session):
        return "Limits"

    def get_qmf_results(self, session):
        values = self.get_data_values(session)
        return self.table.adapter.get_qmf_results(values)

class LimitFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Negotiator

        super(LimitFrame, self).__init__(app, name, cls)

        self.set_limit = NegotiatorLimitTask(app, self)

class NegotiatorLimitTask(ObjectFrameTask):
    def __init__(self, app, frame):
        super(NegotiatorLimitTask, self).__init__(app, frame)

        self.form = NegotiatorLimitForm(app, self.name, self)

    def get_title(self, session):
        return "Set Limit"

    def do_enter(self, session, osession):
        self.form.limit_name.set(session, self.form.limit_name.get(osession))
        self.form.limit_max.set(session, self.form.limit_max.get(osession))

    def do_invoke(self, invoc, negotiator, limit_name, limit_max):
        
        def do_reconfig(self, invoc, negotiator):
            call_async(invoc.make_callback(), 
                       self.app.remote.reconfig, negotiator)

        # Use a custom callback so we can launch reconfig() as a
        # second asynchronous task if set_limit succeeds and let that
        # task run the completion routine for the TaskInvocation.
        # If there is a failure here, however, pass the results
        # directly to the TaskInvocation callback and let the task
        # end with an error status.
        def my_callback(*args):
            if invoc.is_success(*args):
                # Have to be careful here, because we are inside the
                # callback handling method of the qmf console if we
                # are using qmf.  So we need to launch a thread, 
                # because if we don't we have to worry about the 
                # implementation in qmfoperations.py and the console
                # and whether relevant code is re-entrant
                do_reconfig(self, invoc, negotiator)
            else:
                invoc.make_callback()(*args)

        limit_max = float(limit_max)
        self.app.remote.set_limit(negotiator, limit_name, limit_max, 
                                  callback=my_callback)

class NegotiatorLimitForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(NegotiatorLimitForm, self).__init__(app, name, task)

        self.limit_name = self.LimitName(app, "name")
        self.add_field(self.limit_name)

        self.limit_max = self.LimitMax(app, "max")
        self.limit_max.required = True
        self.add_field(self.limit_max)
                       
    def process_submit(self, session):
        new_max_value = self.limit_max.input.get(session)
        unlimited_check_value = self.limit_max.checkbox.param.get(session)
        
        self.limit_max.validate(session)
        if not self.errors.get(session):
            if new_max_value.lower() in ("unlimited", "na", "n/a") or float(new_max_value) >= LIMIT_FLOAT_VALUE_FOR_UNLIMITED:
                self.limit_max.set(session, LIMIT_FLOAT_VALUE_FOR_UNLIMITED)
            elif float(new_max_value) < 0:
                self.limit_max.set(session, 0)
            else:
                self.limit_max.set(session, new_max_value)

        if not self.errors.get(session):
            limit_name = self.limit_name.get(session)
            limit_max = self.limit_max.get_float_value(session)
            negotiator = self.object.get(session)

            self.task.invoke(session, negotiator, limit_name, limit_max)
            self.task.exit_with_redirect(session)

    def render_form_class(self, session):
        return " ".join((super(NegotiatorLimitForm, self).render_form_class(session), "mform"))

    class StringFieldWithCheckbox(StringField):
        def __init__(self, app, name):
            super(NegotiatorLimitForm.StringFieldWithCheckbox, self).__init__(app, name)
            self.button_tmpl = WidgetTemplate(self, "input_with_checkbox_html")
            
            self.checkbox = CheckboxInput(app, "unlimitedcheck")
            self.add_child(self.checkbox)
            
        def do_render(self, session):
            writer = Writer()
            self.button_tmpl.render(writer, session)
            return writer.to_string()       
        
        def render_field_value(self,session):
            return self.input.get(session)
        
        def render_field_name(self,session):
            return self.input.param.path  
        
        def render_is_readonly(self, session):
            retval = ""
            if self.input.get(session) == "Unlimited":
                retval = "readonly='readonly'"            
            return retval
        
        def render_is_checked(self, session):
            retval = ""
            if self.input.get(session) == "Unlimited":
                retval = "checked='checked'"            
            return retval
        
        def render_checkbox_name(self,session):
            return self.checkbox.param.path

        def render_onclick_attr(self, session, *args):
            value = "toggleLimitInput(this, '%s', '%s')" % (self.checkbox.param.path, self.input.param.path) 
            return "onclick=\"%s\"" % value
               
    class LimitName(StringField):
        def __init__(self, app, name):
            super(NegotiatorLimitForm.LimitName, self).__init__(app, name)

            self.input = self.DisabledInput(app, "input")
            self.replace_child(self.input)

        def render_title(self, session):
            return "Limit name"

        class DisabledInput(StringInput):
            # used to override html and css
            pass

    class LimitMax(StringFieldWithCheckbox):            
        def render_title(self, session):
            return "Max Allowance"
        
        def get(self,session):
            # this gets the value for display
            value = self.input.get(session)
            if value >= LIMIT_FLOAT_VALUE_FOR_UNLIMITED:
                value = "Unlimited"
            return value
        
        def get_float_value(self,session):
            # this gets the value sent via QMF to reset the limit
            value = self.input.get(session)
            if float(value) >= LIMIT_FLOAT_VALUE_FOR_UNLIMITED:
                value = LIMIT_FLOAT_VALUE_FOR_UNLIMITED
            return value
        
        def validate(self, session):
            value = self.input.get(session)
            message = None
            if value:
                try:      
                    if value.lower() not in ("unlimited", "na", "n/a"):
                        value = float(value)
                        if value < 0:
                            message = "The '%s' field may not be less than zero" \
                                % self.render_title(session)
                except:
                    message = "The '%s' field must be either \"unlimited\", " \
                        "an integer or a float" % self.render_title(session)

            if message:
                self.form.errors.add(session, FormError(message))
