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

from .form import *
from .frame import *
from .page import *
from .widget import *

_log = logger("disco.account")
_strings = StringCatalog(__file__)

class AccountAdapter:
    @property
    def name(self):
        raise NotImplementedError()

    @property
    def email(self):
        raise NotImplementedError()

    @property
    def last_login(self):
        raise NotImplementedError()

    @property
    def last_logout(self):
        raise NotImplementedError()

    def __repr__(self):
        return fmt_repr(slef, self.name)

class AccountDatabaseSessionAdapter:
    pass

class AccountDatabaseAdapter:
    # @returns AccountAdapter
    # @raises BadCredentialsError
    def login(self, session, name, password):
        raise NotImplementedError()

    def logout(self, session, account):
        raise NotImplementedError()

    # @returns AccountAdapter
    # @raises AccountAlreadyExistsError
    def create(self, session, name, email, password):
        raise NotImplementedError()

    # @raises BadCredentialsError
    def change_email(self, session, account, email, password, new_email):
        raise NotImplementedError()

    # @raises BadCredentialsError
    def change_password(self, session, account, email, password, new_password):
        raise NotImplementedError()

    def __repr__(self):
        return fmt_repr(self)

class AccountAlreadyExistsError(Exception):
    pass

class BadCredentialsError(Exception):
    pass

class AccountFrame(PageFrame):
    def __init__(self, app, name):
        super().__init__(app, name)

        self.database_adapter = None

        self.view_page = AccountView(self, "view")
        self.login_page = AccountLogin(self, "login")
        self.logout_page = AccountLogout(self, "logout")
        self.create_page = AccountCreate(self, "create")
        self.change_email_page = AccountChangeEmail(self, "change-email")
        self.change_password_page = AccountChangePassword \
            (self, "change-password")

        self.default_page = self.view_page

    def init(self):
        super().init()

        assert self.database_adapter is not None

    def process(self, request):
        if request.session.account is None:
            if request.page not in (self.login_page, self.create_page):
                return self.login_page.get_href(request)

class AccountView(Page):
    def get_title(self, request):
        return "Account"

    @xml
    def render_properties(self, request):
        props = (
            ("User name", xml_escape(request.session.account.name)),
            ("Last login", fmt_datetime(request.session.account.last_login)),
            ("Last logout", fmt_datetime(request.session.account.last_logout)),
        )

        return html_property_list(props)

    def render_account_name(self, request):
        return request.session.account.name

    def render_change_email_href(self, request):
        return self.frame.change_email_page.get_href(request)

    def render_change_password_href(self, request):
        return self.frame.change_password_page.get_href(request)

class AccountLogin(FormPage):
    def __init__(self, frame, name):
        super().__init__(frame, name)

        self.name_input = StringInput(StringParameter(self, "name"))
        self.name_input.title = "User name"

        self.password_input = SecretInput(SecretParameter(self, "password"))
        self.password_input.title = "Password"

        self.exit_input.default_value = "/" # XXX

    def get_title(self, request):
        return "Log in"

    def process_continue(self, request):
        name = self.name_input.get(request)
        password = self.password_input.get(request)

        request.session.reset_id()

        try:
            account = self.frame.database_adapter.login(request, name, password)
        except BadCredentialsError:
            request.add_error("Wrong user name or password")

        request.check_errors()
        request.session.account = account

    def render_create_href(self, request):
        return self.frame.create_page.get_href(request)

class AccountLogout(FormPage):
    def get_title(self, request):
        return "Log out"

    def do_process(self, request):
        assert request.session.account is not None

        self.frame.database_adapter.logout(request, request.session.account)

        request.session.reset_id()
        request.session.account = None
        request.session.result_message = "You are now logged out"

        return self.app.get_href(request)

class AccountCreate(FormPage):
    def __init__(self, frame, name):
        super().__init__(frame, name)

        self.name_input = StringInput(StringParameter(self, "name"))
        self.name_input.title = "User name"

        self.email_input = StringInput(SecretParameter(self, "email"))
        self.email_input.title = "Email address"

        self.confirm_email_input = StringInput \
            (SecretParameter(self, "confirm_email"))
        self.confirm_email_input.title = "Confirm email address"

        self.password_input = SecretInput(SecretParameter(self, "password"))
        self.password_input.title = "Password"

        self.confirm_password_input = SecretInput \
            (SecretParameter(self, "confirm_password"))
        self.confirm_password_input.title = "Confirm password"

        self.exit_input.default_value = "/" # XXX

    def get_title(self, request):
        return "Create account"

    def process_continue(self, request):
        name = self.name_input.get(request)
        email = self.email_input.get(request)
        confirm_email = self.confirm_email_input.get(request)
        password = self.password_input.get(request)
        confirm_password = self.confirm_password_input.get(request)

        if email != confirm_email:
            msg = "Confirmation email address does not match"
            self.confirm_email_input.add_error(request, msg)

        if password != confirm_password:
            msg = "Confirmation password does not match"
            self.confirm_password_input.add_error(request, msg)

        request.check_errors()

        try:
            account = self.frame.database_adapter.create \
                (request, name, email, password)
        except AccountAlreadyExistsError:
            request.add_error("An account with this name already exists")

        request.check_errors()
        request.session.reset_id()
        request.session.account = account

    def render_login_href(self, request):
        return self.frame.login_page.get_href(request)

class AccountChangeForm(FormPage):
    def __init__(self, frame, name):
        super().__init__(frame, name)

        self.email_input = StringInput(StringParameter(self, "email"))
        self.email_input.title = "Email address"

        self.password_input = SecretInput(SecretParameter(self, "password"))
        self.password_input.title = "Password"

class AccountChangeEmail(AccountChangeForm):
    def __init__(self, frame, name):
        super().__init__(frame, name)

        self.email_input.title = "Current email address"

        self.new_email_input = StringInput(StringParameter(self, "new_email"))
        self.new_email_input.title = "New email address"

        self.confirm_new_email_input = StringInput \
            (StringParameter(self, "confirm_new_email"))
        self.confirm_new_email_input.title = "Confirm new email address"

    def get_title(self, request):
        return "Change email address"

    def process_continue(self, request):
        email = self.email_input.get(request)
        password = self.password_input.get(request)
        new_email = self.new_email_input.get(request)
        confirm_new_email = self.confirm_new_email_input.get(request)

        if new_email != confirm_new_email:
            msg = "Confirmation email address does not match"
            self.confirm_new_email_input.add_error(request, msg)

        request.check_errors()
        request.session.reset_id()

        try:
            self.frame.database_adapter.change_email \
                (request, request.session.account, email, password, new_email)
        except BadCredentialsError:
            request.add_error("Wrong email or password")

        request.check_errors()
        request.session.result_message = "Email address changed"

class AccountChangePassword(AccountChangeForm):
    def __init__(self, frame, name):
        super().__init__(frame, name)

        self.password_input.title = "Current password"

        self.new_password_input = SecretInput \
            (SecretParameter(self, "new_password"))
        self.new_password_input.title = "New password"

        self.confirm_password_input = SecretInput \
            (SecretParameter(self, "confirm_password"))
        self.confirm_password_input.title = "Confirm new password"

    def get_title(self, request):
        return "Change password"

    def process_continue(self, request):
        email = self.email_input.get(request)
        password = self.password_input.get(request)
        new_password = self.new_password_input.get(request)
        confirm_password = self.confirm_password_input.get(request)

        if new_password != confirm_password:
            msg = "Confirmation password does not match"
            self.confirm_password_input.add_error(request, msg)

        request.check_errors()
        request.session.reset_id()

        try:
            self.frame.database_adapter.change_password \
                (request, request.session.account, email, password, new_password)
        except BadCredentialsError:
            request.add_error("Wrong email or password")

        request.check_errors()
        request.session.result_message = "Password changed"
