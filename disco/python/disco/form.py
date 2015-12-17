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

from .page import *

_log = logger("disco.form")
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
    @group Session attributes: set_nonce
    """
    def __init__(self, frame, name):
        super().__init__(frame, name)

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
        super().init()

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

    def process(self, request):
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

        self.load_parameters(request)
        self.check_errors(request)

        redirect = self.do_process(request)

        return redirect

    def do_process(self, request):
        request_method = request._app_request.method

        if request_method == "GET":
            self.set_nonce(request)

            return self.process_view(request)

        if request_method == "POST":
            self.check_nonce(request)

            button = self.button_param.get(request)

            try:
                redirect = button.process(request)
            except PageRequestError:
                redirect = None

            return redirect

        raise Exception("Unexpected request method")

    # A per-view form authentication code
    def set_nonce(self, request):
        nonce = unique_id()

        self.nonce_input.set(request, nonce)

        with request.session.lock:
            request.session.form_nonce = nonce

    def check_nonce(self, request):
        """
        Raise a processing error if the form submission is not authentic

        @see: L{set_nonce}

        @raise ApplicationRequestError: If the form nonce is not the expected
        one
        """

        server_nonce = request.session.form_nonce
        form_nonce = self.nonce_input.get(request)

        self.set_nonce(request)

        if server_nonce is None or server_nonce != form_nonce:
            raise ApplicationRequestError("Form authentication failed")

    def get_href(self, request, exit=None):
        path = super().get_href(request)

        if exit is None:
            exit = request._app_request.uri

        return encode_href(path, exit=exit)

    def process_view(self, request):
        pass

    def process_continue(self, request):
        pass

    def process_exit(self, request):
        pass

    @xml
    def render_hidden_inputs(self, request):
        out = list()

        for input in self.hidden_inputs:
            out.append(input.render(request))

        return "".join(out)

    @xml
    def render_errors(self, request):
        errors = self.get_errors(request)

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
    def render_inputs(self, request):
        out = list()

        for input in self.inputs:
            out.append(input.render(request))

        return "".join(out)

    @xml
    def render_buttons(self, request):
        out = list()

        for button in self.buttons:
            out.append(button.render(request))

        return "".join(out)

class _FormNonceParameter(SecretParameter):
    pass

class _FormExitParameter(StringParameter):
    def get_default_value(self, request):
        if self.default_value is None:
            return self.page.frame.get_href(request)

        return self.default_value

class _FormContinueParameter(StringParameter):
    def get_default_value(self, request):
        return self.page.exit_input.get(request)

class _FormButtonParameter(LookupParameter):
    def __init__(self, page, name):
        super().__init__(page, name)

        self.required = False
        self.dictionary = self.page.buttons_by_value

class _FormElement(RenderObject):
    def __init__(self, parameter):
        super().__init__()

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

    def get(self, request):
        return self.parameter.get(request)

    def set(self, request, obj):
        self.parameter.set(request, obj)

    def get_errors(self, request):
        return self.parameter.get_errors(request)

    def add_error(self, request, message):
        self.parameter.add_error(request, message)

    def render_id(self, request):
        return "%s-input" % self.name

    def render_title(self, request):
        return self.title

    def render_description(self, request):
        return self.description

    def render_name(self, request):
        return self.name

    def render_tab_index(self, request):
        return str(self.tab_index)

    @xml
    def render_disabled_attr(self, request):
        if self.disabled:
            return "disabled=\"disabled\""

    @xml
    def render_autofocus_attr(self, request):
        if self.autofocus:
            return "autofocus=\"autofocus\""

    @xml
    def render_errors(self, request):
        errors = self.parameter.get_errors(request)

        if not errors:
            return

        messages = [x.message for x in errors]
        messages = "; ".join(messages)
        messages = xml_escape(messages)
            
        return html_div(messages, _class="input-errors")

    @xml
    def render_content(self, request):
        raise NotImplementedError()

    def __repr__(self):
        return fmt_repr(self, self.name)

class HiddenInput(_FormElement):
    def __init__(self, parameter):
        super().__init__(parameter)

        assert self.app._initialized is False
        assert self.name not in self.page.hidden_inputs_by_name

        self.page.hidden_inputs.append(self)
        self.page.hidden_inputs_by_name[self.name] = self

    def delete(self):
        super().delete()

        self.page.hidden_inputs.remove(self)
        del self.page.hidden_inputs_by_name[self.name]

    @xml
    def render(self, request):
        obj = self.parameter.get(request)

        if obj is None:
            return

        strings = self.parameter.marshal(request, obj)
        out = list()

        for string in strings:
            out.append(html_input(self.name, string, "hidden"))

        return "".join(out)

class FormInput(_FormElement):
    def __init__(self, parameter):
        super().__init__(parameter)

        self.content_template = RenderTemplate(self, "content")

        assert self.app._initialized is False
        assert self.name not in self.page.inputs_by_name

        self.page.inputs.append(self)
        self.page.inputs_by_name[self.name] = self

    def delete(self):
        super().delete()

        self.page.inputs.remove(self)
        del self.page.inputs_by_name[self.name]

    def init(self):
        super().init()

        meth_name = "render_%s_input" % self.name

        def meth(obj, request):
            return self.render(request)

        self.add_render_method(meth_name, xml(meth))

        self.bind_templates()

class StringInput(FormInput):
    def __init__(self, parameter):
        super().__init__(parameter)

        # XXX
        #assert isinstance(parameter, StringParameter), parameter

    def render_type(self, request):
        return "text"

    def render_value(self, request):
        obj = self.get(request)

        if obj is None:
            return

        return self.parameter.marshal(request, obj)[0]

class SecretInput(StringInput):
    def render_type(self, request):
        return "password"

class Selector(FormInput):
    # @returns an iterable of SelectorItems
    def get_items(self, request):
        raise NotImplementedError()

class SelectorItem:
    def __init__(self, _object, value, title):
        self.object = _object
        self.value = value
        self.title = title

class DropdownSelector(Selector):
    @xml
    def render_options(self, request):
        out = list()
        selection = self.get(request)

        for item in self.get_items(request):
            title = xml_escape(item.title)
            value = item.value
            selected = item.object == selection

            out.append(html_option(title, value, selected))

        return "".join(out)

class RadioSelector(FormInput):
    @xml
    def render_inputs(self, request):
        out = list()
        selection = self.get(request)

        for item in self.get_items(request):
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
        super().__init__(page.button_param)

        self.value = value

        assert self.app._initialized is False
        assert self.value not in self.page.buttons_by_value

        self.page.buttons.append(self)
        self.page.buttons_by_value[self.value] = self

    def delete(self):
        self.page.buttons.remove(self)
        del self.page.buttons_by_value[self.value]

    def init(self):
        super().init()

        meth_name = "render_{}_button".format(self.value)

        def meth(obj, request):
            return self.render(request)

        self.add_render_method(meth_name, xml(meth))

        self.bind_templates()

    def process(self, request):
        raise NotImplementedError()

    def render_id(self, request):
        return "{}-button".format(self.value)

    def render_value(self, request):
        return self.value

    def __repr__(self):
        return fmt_repr(self, self.value)

class ContinueButton(FormButton):
    def process(self, request):
        self.page.validate_parameters(request)
        self.page.check_errors(request)

        redirect = self.page.process_continue(request)

        if redirect is None:
            redirect = self.page.continue_input.get(request)

        return redirect

    def render_title(self, request):
        if self.title is not None:
            return self.title

        return "Continue"

class ExitButton(FormButton):
    def process(self, request):
        redirect = self.page.process_exit(request)

        if redirect is None:
            redirect = self.page.exit_input.get(request)

        return redirect

    def render_title(self, request):
        if self.title is not None:
            return self.title

        return "Exit"

class ConfirmForm(FormPage):
    pass
