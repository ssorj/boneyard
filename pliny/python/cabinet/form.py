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

from page import *

_log = logger("cabinet.form")
_strings = StringCatalog(__file__)

# Topics
#
# - inputs and buttons
# - hidden inputs
# - Continue and exit
# - Form GET verus POST
# - check_errors: PageError stops execution
# - Successful form submission results in a redirect and prevents
#   rendering
#
# XXX _FormElement -> FormElement
class FormPage(Page):
    """
    @group Request processing: check_nonce
    @group Client attributes: set_nonce
    """
    def __init__(self, frame, name):
        super(FormPage, self).__init__(frame, name)

        self.body_template.delete()
        self.body_template = RenderTemplate(self, "body")

        self.hidden_inputs = list()
        self.hidden_inputs_by_name = dict()

        self.inputs = list()
        self.inputs_by_name = dict()

        self.nonce_input = HiddenInput(_FormNonceParameter(self, "nonce"))
        self.continue_input = HiddenInput \
            (_FormContinueParameter(self, "continue"))
        self.exit_input = HiddenInput(_FormExitParameter(self, "exit"))

        self.buttons = list()
        self.buttons_by_value = dict()

        self.button_param = _FormButtonParameter(self, "button")

        self.continue_button = ContinueButton(self, "continue")
        self.exit_button = ExitButton(self, "exit")

    def init(self):
        super(FormPage, self).init()

        autofocused_already = False

        for input in self.inputs:
            input.init()

            if input.autofocus is True:
                autofocused_already = True

        if not autofocused_already:
            for input in self.inputs:
                input.autofocus = True
                break

        for button in self.buttons:
            button.init()

    def process(self, session):
        """
        Processing logic executed before the page is rendered

        This internally calls L{load_parameters}.  Unlike L{Page.process},
        it does not not call L{validate_parameters}.  That processing is
        deferred until it is determined that the request is a form POST, as
        opposed to a form GET.

        Also unlike L{Page.process}, instead of triggering an exception,
        validation errors are displayed and the user is prompted for revised
        input.

        @see: L{Page.receive}

        @rtype: basestring
        @return: A redirect URI or None
        """

        _log.debug("Processing %s", self)

        self.load_parameters(session)
        self.check_errors(session)

        redirect = self.do_process(session)

        return redirect

    def do_process(self, session):
        request_method = session.request.method

        if request_method == "GET":
            self.set_nonce(session)

            return self.process_view(session)

        if request_method == "POST":
            self.check_nonce(session)

            button = self.button_param.get(session)

            try:
                redirect = button.process(session)
            except PageSessionError:
                redirect = None

            return redirect

        raise Exception("Unexpected request method")

    # A per-view form authentication code
    def set_nonce(self, session):
        nonce = unique_id()

        self.nonce_input.set(session, nonce)
        self.get_client_session(session).form_nonce = nonce

    def check_nonce(self, session):
        """
        Raise a processing error if the form submission is not authentic

        @see: L{set_nonce}

        @raise ApplicationRequestError: If the form nonce is not the expected
        one
        """

        client = self.get_client_session(session)

        server_nonce = client.form_nonce
        form_nonce = self.nonce_input.get(session)

        self.set_nonce(session)

        if server_nonce is None or server_nonce != form_nonce:
            raise ApplicationRequestError("Form authentication failed")

    def get_href(self, session, exit=None):
        path = super(FormPage, self).get_href(session)

        if exit is None:
            exit = session.request.uri

        return encode_href(path, exit=exit)

    def process_view(self, session):
        pass

    def process_continue(self, session):
        pass

    def process_exit(self, session):
        pass

    @xml
    def render_hidden_inputs(self, session):
        out = list()

        for input in self.hidden_inputs:
            out.append(input.render(session))

        return "".join(out)

    @xml
    def render_errors(self, session):
        errors = self.get_errors(session)

        if not errors:
            return

        if len(errors) == 1:
            error = errors[0]
            msg = xml_escape(error.message)
            return html_div(msg, id="form-errors")

        out = list()
        out.append(html_open("ul"))

        for error in errors:
            msg = xml_escape(error.message)
            out.append(html_li(msg))

        out.append(html_close("ul"))
        out = "".join(out)

        return html_div(out, id="form-errors")

    @xml
    def render_inputs(self, session):
        out = list()

        for input in self.inputs:
            out.append(input.render(session))

        return "".join(out)

    @xml
    def render_buttons(self, session):
        out = list()

        for button in self.buttons:
            out.append(button.render(session))

        return "".join(out)

class _FormNonceParameter(SecretParameter):
    pass

class _FormExitParameter(StringParameter):
    def get_default_value(self, session):
        if self.default_value is None:
            return self.page.frame.get_href(session)

        return self.default_value

class _FormContinueParameter(StringParameter):
    def get_default_value(self, session):
        return self.page.exit_input.get(session)

class _FormButtonParameter(LookupParameter):
    def __init__(self, page, name):
        super(_FormButtonParameter, self).__init__(page, name)

        self.required = False
        self.dictionary = self.page.buttons_by_value

class _FormElement(RenderObject):
    def __init__(self, parameter):
        super(_FormElement, self).__init__()

        assert isinstance(parameter, Parameter)
        assert isinstance(parameter.page, FormPage)

        self.parameter = parameter

        self.title = None
        self.description = None
        self.tab_index = 100
        self.disabled = False
        self.autofocus = False

    def delete(self):
        self.parameter.delete()

    @property
    def page(self):
        return self.parameter.page

    @property
    def name(self):
        return self.parameter.name

    @property
    def app(self):
        return self.parameter.app

    @property
    def default_value(self):
        return self.parameter.default_value

    @default_value.setter
    def default_value(self, value):
        self.parameter.default_value = value

    def get(self, session):
        return self.parameter.get(session)

    def set(self, session, obj):
        self.parameter.set(session, obj)

    def get_errors(self, session):
        return self.parameter.get_errors(session)

    def add_error(self, session, message):
        self.parameter.add_error(session, message)

    def render_id(self, session):
        return "%s-input" % self.name

    def render_title(self, session):
        return self.title

    def render_description(self, session):
        return self.description

    def render_name(self, session):
        return self.name

    def render_tab_index(self, session):
        return str(self.tab_index)

    @xml
    def render_disabled_attr(self, session):
        if self.disabled:
            return "disabled=\"disabled\""

    @xml
    def render_autofocus_attr(self, session):
        if self.autofocus:
            return "autofocus=\"autofocus\""

    @xml
    def render_errors(self, session):
        errors = self.parameter.get_errors(session)

        if not errors:
            return

        messages = [x.message for x in errors]
        messages = "; ".join(messages)
        messages = xml_escape(messages)
            
        return html_div(messages, _class="input-errors")

    @xml
    def render_content(self, session):
        raise NotImplementedError()

    def __repr__(self):
        args = self.__class__.__name__, self.name
        return "%s(%s)" % args

class HiddenInput(_FormElement):
    def __init__(self, parameter):
        super(HiddenInput, self).__init__(parameter)

        assert self.app._initialized is False
        assert self.name not in self.page.hidden_inputs_by_name

        self.page.hidden_inputs.append(self)
        self.page.hidden_inputs_by_name[self.name] = self

    def delete(self):
        super(HiddenInput, self).delete()

        self.page.hidden_inputs.remove(self)
        del self.page.hidden_inputs_by_name[self.name]

    @xml
    def render(self, session):
        obj = self.parameter.get(session)

        if obj is None:
            return

        strings = self.parameter.marshal(session, obj)
        out = list()

        for string in strings:
            out.append(html_input(self.name, string, "hidden"))

        return "".join(out)

class FormInput(_FormElement):
    def __init__(self, parameter):
        super(FormInput, self).__init__(parameter)

        self.content_template = RenderTemplate(self, "content")

        assert self.app._initialized is False
        assert self.name not in self.page.inputs_by_name

        self.page.inputs.append(self)
        self.page.inputs_by_name[self.name] = self

    def delete(self):
        super(FormInput, self).delete()

        self.page.inputs.remove(self)
        del self.page.inputs_by_name[self.name]

    def init(self):
        super(FormInput, self).init()

        meth_name = "render_%s_input" % self.name

        def meth(obj, session):
            return self.render(session)

        self.add_render_method(meth_name, xml(meth))

        self.bind_templates()

class StringInput(FormInput):
    def __init__(self, parameter):
        super(StringInput, self).__init__(parameter)

        # XXX
        #assert isinstance(parameter, StringParameter), parameter

    def render_type(self, session):
        return "text"

    def render_value(self, session):
        obj = self.get(session)

        if obj is None:
            return

        return self.parameter.marshal(session, obj)[0]

class SecretInput(StringInput):
    def render_type(self, session):
        return "password"

class Selector(FormInput):
    # @returns an iterable of SelectorItems
    def get_items(self, session):
        raise NotImplementedError()

class SelectorItem(object):
    def __init__(self, _object, value, title):
        self.object = _object
        self.value = value
        self.title = title

class DropdownSelector(Selector):
    @xml
    def render_options(self, session):
        out = list()
        selection = self.get(session)

        for item in self.get_items(session):
            title = xml_escape(item.title)
            value = item.value
            selected = item.object == selection

            out.append(html_option(title, value, selected))

        return "".join(out)

class RadioSelector(FormInput):
    @xml
    def render_inputs(self, session):
        out = list()
        selection = self.get(session)

        for item in self.get_items(session):
            value = item.value
            checked = item.object == selection
            title = xml_escape(item.title)

            out.append(html_open("div", _class="radio-selector-item"))
            out.append(html_radio_input(self.name, value, checked))
            out.append(html_elem("label", title))
            out.append(html_close("div"))

        return "".join(out)

class FormButton(_FormElement):
    def __init__(self, page, value):
        super(FormButton, self).__init__(page.button_param)

        self.value = value

        assert self.app._initialized is False
        assert self.value not in self.page.buttons_by_value

        self.page.buttons.append(self)
        self.page.buttons_by_value[self.value] = self

    def delete(self):
        self.page.buttons.remove(self)
        del self.page.buttons_by_value[self.value]

    def init(self):
        super(FormButton, self).init()

        meth_name = "render_%s_button" % self.value

        def meth(obj, session):
            return self.render(session)

        self.add_render_method(meth_name, xml(meth))

        self.bind_templates()

    def process(self, session):
        raise NotImplementedError()

    def render_id(self, session):
        return "%s-button" % self.value

    def render_value(self, session):
        return self.value

    def __repr__(self):
        args = self.__class__.__name__, self.value
        return "%s(%s)" % args

class ContinueButton(FormButton):
    def process(self, session):
        self.page.validate_parameters(session)
        self.page.check_errors(session)

        redirect = self.page.process_continue(session)

        if redirect is None:
            redirect = self.page.continue_input.get(session)

        return redirect

    def render_title(self, session):
        if self.title is not None:
            return self.title

        return "Continue"

class ExitButton(FormButton):
    def process(self, session):
        redirect = self.page.process_exit(session)

        if redirect is None:
            redirect = self.page.exit_input.get(session)

        return redirect

    def render_title(self, session):
        if self.title is not None:
            return self.title

        return "Exit"

class ConfirmForm(FormPage):
    pass
