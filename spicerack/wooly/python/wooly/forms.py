from parameters import *
from resources import *
from util import *
from widgets import *
from wooly import *

log = logging.getLogger("wooly.forms")
strings = StringCatalog(__file__)

class Form(Widget):
    def __init__(self, app, name):
        super(Form, self).__init__(app, name)

        self.errors = Attribute(app, "errors")
        self.add_attribute(self.errors)

        self.form_params = set()

    def validate(self, session):
        log.debug("Validating %s", self)
        
    def render_hidden_inputs(self, session):
        writer = Writer()

        params = set(session.page.get_page_parameters(session))
        params.difference_update(self.form_params)

        for param in params:
            key = param.path

            if param.is_collection:
                collection = session.get(key)

                if collection:
                    for value in collection:
                        svalue = param.marshal(value)
                        self.write_hidden_input(key, svalue, writer)
            elif param.is_dictionary:
                pass
            else:
                value = session.get(key)
                default = param.get_default(session)

                if value not in (default, None):
                    svalue = param.marshal(value)
                    self.write_hidden_input(key, svalue, writer)

        return writer.to_string()

    def write_hidden_input(self, name, value, writer):
        writer.write("<input type=\"hidden\" name=\"%s\" value=\"%s\"/>" \
                     % (name, escape_entity(value)))

class FormError(object):
    def __init__(self, message):
        self.message = xml_escape(message)

    def get_message(self, session):
        return self.message

class FormErrorSet(ItemSet):
    def __init__(self, app, name):
        super(FormErrorSet, self).__init__(app, name)

        self.set_item_widget(FormErrorWidget(app, "item"))

    def init(self):
        super(FormErrorSet, self).init()

        for anc in self.ancestors:
            if isinstance(anc, Form):
                self.form = anc

        assert self.form, "Not inside a form"

    def get_items(self, session):
        return self.form.errors.get(session)

    def do_render(self, session):
        items = self.get_items(session)

        if items:
            return super(FormErrorSet, self).do_render(session)

class FormErrorWidget(ItemWidget):
    def render_content(self, session):
        item = self.item.get(session)
        return item.get_message(session)

class FormInput(Widget):
    def __init__(self, app, name, param):
        super(FormInput, self).__init__(app, name)

        self.param = param
        self.tab_index = 100
        self.disabled = False

    def init(self):
        super(FormInput, self).init()

        assert self.param # Parameter not set
        assert isinstance(self.param, Parameter)

        for anc in self.ancestors:
            if isinstance(anc, Form):
                self.form = anc

        assert self.form # Not inside a form

        self.form.form_params.add(self.param)

    def get(self, session):
        return self.param.get(session)

    def set(self, session, value):
        return self.param.set(session, value)

    def get_default(self, session):
        return self.param.get_default(session)

    def render_name(self, session):
        return self.param.path

    def render_value(self, session):
        return escape_entity(self.param.marshal(self.param.get(session)))

    def render_tab_index(self, session):
        return self.tab_index

    def render_disabled_attr(self, session):
        return self.disabled and "disabled=\"disabled\"" or None

class MissingValueError(FormError):
    def __init__(self, widget):
        super(MissingValueError, self).__init__(None)

        self.widget = widget

    def get_message(self, session):
        title = self.widget.render_title(session)
        return "The '%s' field must have a value" % title

class QuoteValueError(FormError):
    def __init__(self, widget):
        super(QuoteValueError, self).__init__(None)

        self.widget = widget

    def get_message(self, session):
        title = self.widget.render_title(session)
        return "The '%s' field may not contain double quotes" % title

class XMLValueError(FormError):
    def __init__(self, widget):
        super(XMLValueError, self).__init__(None)

        self.widget = widget

    def get_message(self, session):
        title = self.widget.render_title(session)
        return "The '%s' field may not contain XML special characters" % title

class EmptyInputError(FormError):
    def __init__(self):
        super(EmptyInputError, self).__init__("This value is required")

class ScalarInput(FormInput):
    def __init__(self, app, name, param):
        super(ScalarInput, self).__init__(app, name, param)

        self.size = 32
        self.title = None

    def render_size(self, session):
        return self.size

    def render_title(self, session):
        if self.title:
            return "title=\"%s\"" % self.title

class StringInput(ScalarInput):
    def __init__(self, app, name):
        super(StringInput, self).__init__(app, name, None)

        self.param = StringParameter(app, "param")
        self.add_parameter(self.param)

        self.size = 30

class MultilineStringInput(StringInput):
    def __init__(self, app, name):
        super(MultilineStringInput, self).__init__(app, name)

        self.rows = 4
        self.columns = 32

    def render_rows(self, session):
        return self.rows

    def render_columns(self, session):
        return self.columns

class PasswordInput(StringInput):
    pass

# XXX Why does this have a boolean param?  Shouldn't the name suggest
# that somehow?  Would some folks want a hidden input with a different
# param?  I think this needs to take a param
class HiddenInput(ScalarInput):
    def __init__(self, app, name):
        super(HiddenInput, self).__init__(app, name, None)

        self.param = BooleanParameter(app, "param")
        self.add_parameter(self.param)

class IntegerInput(ScalarInput):
    def __init__(self, app, name):
        super(IntegerInput, self).__init__(app, name, None)

        self.param = IntegerParameter(app, "param")
        self.add_parameter(self.param)

        self.size = 15

class FloatInput(ScalarInput):
    def __init__(self, app, name):
        super(FloatInput, self).__init__(app, name, None)

        self.param = FloatParameter(app, "param")
        self.add_parameter(self.param)

        self.size = 15

class CheckboxInput(FormInput):
    def __init__(self, app, name, param=None):
        super(CheckboxInput, self).__init__(app, name, param)

        if not self.param:
            self.param = VoidBooleanParameter(app, "param")
            self.add_parameter(self.param)

    def render_onclick_attr(self, session):
        pass

    def render_checked_attr(self, session):
        if self.get(session):
            return "checked=\"checked\""

class RadioInput(FormInput):
    def __init__(self, app, name, param):
        super(RadioInput, self).__init__(app, name, param)

        self.value = name

    def render_value(self, session):
        return self.value

    def render_checked_attr(self, session):
        value = self.get(session)

        if value and value == self.value:
            return "checked=\"checked\""

class FormButton(FormInput):
    def __init__(self, app, name):
        super(FormButton, self).__init__(app, name, None)

        self.param = BooleanParameter(app, "invoked")
        self.add_parameter(self.param)

    def do_process(self, session):
        if self.get(session):
            self.set(session, False)

            self.process_submit(session)

    def process_submit(self, session):
        pass

    def render_value(self, session):
        branch = session.branch()

        self.set(branch, True)

        return super(FormButton, self).render_value(branch)

    def render_type(self, session):
        return "submit"

    def render_onclick(self, session):
        return "click_button"

class CheckboxInputSet(FormInput, ItemSet):
    def render_item_value(self, session, item):
        return None

    def render_item_checked_attr(self, session, item):
        return None

class FormInputItemSet(FormInput, ItemSet):
    def render_item_value(self, session, item):
        return item.value

    def render_item_title(self, session, item):
        return item.title

    def render_item_description(self, session, item):
        return item.description

    def render_item_disabled_attr(self, session, item):
        if item.disabled:
            return "disabled=\"disabled\""

class FormInputItem(object):
    def __init__(self, value, title=None):
        self.value = value
        self.title = title
        self.description = None
        self.disabled = False

class RadioItemSet(FormInputItemSet):
    def render_item_type(self, session, item):
        return "radio"

    def render_item_checked_attr(self, session, item):
        if item.value == self.get(session):
            return "checked=\"checked\""

class RadioItem(FormInputItem):
    pass

class CheckboxItemSet(FormInputItemSet):
    def __init__(self, app, name, item_parameter):
        super(CheckboxItemSet, self).__init__(app, name, None)

        self.param = ListParameter(app, "param", item_parameter)
        self.add_parameter(self.param)

    def render_item_type(self, session, item):
        return "checkbox"

    def render_item_checked_attr(self, session, item):
        if item.value in self.get(session):
            return "checked=\"checked\""

class CheckboxItem(FormInputItem):
    pass

class RadioInputSet(ScalarInput, ItemSet):
    def render_item_value(self, session):
        return None

    def render_item_checked_attr(self, session):
        return None

class OptionInputSet(ScalarInput, ItemSet):
    def render_item_value(self, session, item):
        return None

    def render_item_selected_attr(self, session, item):
        return None
    
    def render_onchange(self, session):
        return None
    
class FormField(Widget):
    def __init__(self, app, name):
        super(FormField, self).__init__(app, name)

        self.form = None

        self.required = False
        self.help = None

    def init_computed_values(self):
        super(FormField, self).init_computed_values()

        for anc in self.ancestors:
            if isinstance(anc, Form):
                self.form = anc

    def seal(self):
        super(FormField, self).seal()

        assert self.form # Not inside a form

    def validate(self, session):
        pass

    def render_required(self, session):
        if self.required:
            return "<span style=\"color: #c33\">*</span>"

    def render_help(self, session):
        return self.help

class LabelFormField(FormField):
    def __init__(self, app, name):
        super(LabelFormField, self).__init__(app, name)
        self.title = ""
        
    def render_title(self, session):
        return self.title
    
class FormFieldSet(Widget):
    def __init__(self, app, name):
        super(FormFieldSet, self).__init__(app, name)

        self.fields = list()

    def add_field(self, field):
        assert isinstance(field, FormField)

        self.fields.append(field)
        self.add_child(field)

    def validate(self, session):
        for field in self.fields:
            field.validate(session)

    def render_message(self, session):
        pass

    def render_fields(self, session):
        writer = Writer()

        for field in self.fields:
            writer.write(field.render(session))

        return writer.to_string()

class ShowableFieldSet(FormFieldSet):
    def __init__(self, app, name):
        super(ShowableFieldSet, self).__init__(app, name)

    def render(self, session):
        return len(self.fields) and \
            super(ShowableFieldSet, self).render(session) or ""

class Label(FormField):
    ''' this is a special field, with no values, used to show text on a form '''
    def __init__(self, app, name):
        super(Label, self).__init__(app, name)
        self.text = ""
    
    def render_value(self, session):
        return self.text

class ScalarField(FormField):
    def __init__(self, app, name, input):
        super(ScalarField, self).__init__(app, name)

        self.input = input

    def init(self):
        super(ScalarField, self).init()

        assert self.input is not None
        assert isinstance(self.input, ScalarInput)

    def get(self, session):
        return self.input.get(session)

    def set(self, session, value):
        return self.input.set(session, value)

    def validate(self, session):
        super(ScalarField, self).validate(session)

        if self.required:
            value = self.get(session)

            if value is None:
                error = MissingValueError(self)
                self.form.errors.add(session, error)

            if isinstance(value, str):
                value = value.strip()

                if value == "":
                    error = MissingValueError(self)
                    self.form.errors.add(session, error)

    def render_inputs(self, session):
        return self.input.render(session)

class StringField(ScalarField):
    def __init__(self, app, name):
        super(StringField, self).__init__(app, name, None)

        self.input = StringInput(app, "input")
        self.add_child(self.input)

class NoXMLStringField(StringField):
    def validate(self, session):
        super(NoXMLStringField, self).validate(session)

        des = self.get(session)
        if '"' in des:
            error = QuoteValueError(self)
            self.form.errors.add(session, error)

        elif xml_escape(des) != des:
            error = XMLValueError(self)
            self.form.errors.add(session, error)

class MultilineStringField(ScalarField):
    def __init__(self, app, name):
        super(MultilineStringField, self).__init__(app, name, None)

        self.input = MultilineStringInput(app, "input")
        self.add_child(self.input)

class PasswordField(ScalarField):
    def __init__(self, app, name):
        super(PasswordField, self).__init__(app, name, None)

        self.input = PasswordInput(app, "input")
        self.add_child(self.input)

class IntegerField(ScalarField):
    def __init__(self, app, name):
        super(IntegerField, self).__init__(app, name, None)

        self.input = IntegerInput(app, "input")
        self.add_child(self.input)

    def validate(self, session):
        super(IntegerField, self).validate(session)

        value = self.get(session)

        if value:
            try:
                value = int(value)
            except:
                title = self.render_title(session)
                message = "The '%s' field must be an integer" % title
                self.form.errors.add(session, FormError(message))

class RealField(ScalarField):
    def __init__(self, app, name):
        super(RealField, self).__init__(app, name, None)

        self.input = FloatInput(app, "input")
        self.add_child(self.input)

    def validate(self, session):
        super(RealField, self).validate(session)

        value = self.get(session)

        if value:
            try:
                value = float(value)
            except:
                title = self.render_title(session)
                message = "The '%s' field must be an integer or float" % title
                self.form.errors.add(session, FormError(message))

# XXX make this use a RadioInputSet instead?
class RadioField(FormField):
    def __init__(self, app, name, param):
        super(RadioField, self).__init__(app, name)

        self.param = param
        self.options = list()

    def init(self):
        super(RadioField, self).init()

        assert self.param is not None
        assert isinstance(self.param, Parameter)

    def add_option(self, option):
        assert isinstance(option, RadioFieldOption)

        self.options.append(option)
        self.add_child(option)

        option.param = self.param

    def get(self, session):
        return self.param.get(session)

    def set(self, session, value):
        self.param.set(session, value)

    def render_inputs(self, session):
        writer = Writer()

        for option in self.options:
            writer.write(option.render(session))

        return writer.to_string()

class RadioFieldOption(RadioInput):
    pass

class RadioItemSetField(FormField):
    def __init__(self, app, name, param):
        super(RadioItemSetField, self).__init__(app, name)

        self.inputs = self.Inputs(app, "inputs", param)
        self.add_child(self.inputs)

    def get(self, session):
        return self.inputs.get(session)

    def do_get_items(self, session):
        raise Exception("Not implemented")

    class Inputs(RadioItemSet):
        def do_get_items(self, session):
            return self.parent.do_get_items(session)

class CheckboxItemSetField(FormField):
    def __init__(self, app, name, item_parameter):
        super(CheckboxItemSetField, self).__init__(app, name)

        self.inputs = self.Inputs(app, "inputs", item_parameter)
        self.add_child(self.inputs)

    def get(self, session):
        return self.inputs.get(session)

    def do_get_items(self, session):
        raise Exception("Not implemented")

    class Inputs(CheckboxItemSet):
        def do_get_items(self, session):
            return self.parent.do_get_items(session)

class ButtonForm(Form):
    def __init__(self, app, name):
        super(ButtonForm, self).__init__(app, name)

        self.error_display = FormErrorSet(app, "errors")
        self.add_child(self.error_display)

        self.buttons = list()

    def add_button(self, button):
        assert isinstance(button, FormButton)

        self.buttons.append(button)
        self.add_child(button)

    def render_errors(self, session):
        if self.errors.get(session):
            return self.error_display.render(session)

    def render_content(self, session):
        raise Exception("Not implemented")

    def render_buttons(self, session):
        writer = Writer()

        for button in self.buttons:
            writer.write(button.render(session))

        return writer.to_string()

    def render_form_class(self, session):
        return "ButtonForm"

class SubmitForm(ButtonForm):
    def __init__(self, app, name):
        super(SubmitForm, self).__init__(app, name)

        self.return_url = Parameter(app, "return")
        self.add_parameter(self.return_url)

        self.create_submit(app)

        self.cancel_button = self.Cancel(app, "cancel")
        self.cancel_button.tab_index = 200
        self.add_button(self.cancel_button)

    # this is a method so it can be overridden
    def create_submit(self, app):
        self.submit_button = self.Submit(app, "submit")
        self.submit_button.tab_index = 201
        self.add_button(self.submit_button)

    def submit(self, session):
        self.submit_button.set(session, True)

    def cancel(self, session):
        self.cancel_button.set(session, True)

    def do_process(self, session):
        if self.cancel_button.get(session):
            self.cancel_button.set(session, False)

            self.process_cancel(session)
        elif self.submit_button.get(session):
            self.submit_button.set(session, False)

            self.process_submit(session)
        else:
            self.process_display(session)

        super(SubmitForm, self).do_process(session)

    # XXX get rid of this?
    def process_return(self, session):
        url = self.return_url.get(session)
        self.page.redirect.set(session, url)

    def process_cancel(self, session):
        self.process_return(session)

    def process_submit(self, session):
        pass

    def process_display(self, session):
        pass

    def render_cancel_content(self, session):
        return "Cancel"

    def render_submit_content(self, session):
        return "Submit"

    class Cancel(FormButton):
        def render_class(self, session):
            return "cancel"

        def render_content(self, session):
            return self.parent.render_cancel_content(session)

    class Submit(FormButton):
        def render_class(self, session):
            return "submit"

        def render_content(self, session):
            return self.parent.render_submit_content(session)

class FieldSubmitForm(SubmitForm):
    def __init__(self, app, name):
        super(FieldSubmitForm, self).__init__(app, name)

        self.content = FormFieldSet(app, "fields")
        self.add_child(self.content)

    def add_field(self, field):
        self.content.add_field(field)

    def validate(self, session):
        super(FieldSubmitForm, self).validate(session)

        self.content.validate(session)

    def render_content(self, session):
        return self.content.render(session)

class FoldingFieldSubmitForm(SubmitForm):
    def __init__(self, app, name):
        super(FoldingFieldSubmitForm, self).__init__(app, name)

        self.content = Widget(app, "fields")
        self.add_child(self.content)

        self.main_fields = FormFieldSet(app, "main")
        self.content.add_child(self.main_fields)

        self.extra_fields = ShowableFieldSet(app, "extra")
        self.content.add_child(self.extra_fields)

    def add_field(self, field):
        self.main_fields.add_field(field)

    def add_extra_field(self, field):
        self.extra_fields.add_field(field)

    def validate(self, session):
        super(FoldingFieldSubmitForm, self).validate(session)

        self.main_fields.validate(session)
        self.extra_fields.validate(session)

    def render_content(self, session):
        return self.content.render(session)
