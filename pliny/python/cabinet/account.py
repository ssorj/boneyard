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

from form import *
from frame import *

_log = logger("cabinet.account")
_strings = StringCatalog(__file__)

class AccountAdapter(object):
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
        args = self.__class__.__name__, self.name
        return "%s(%s)" % args

class AccountDatabaseSessionAdapter(object):
    pass

class AccountDatabaseAdapter(object):
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
        return self.__class__.__name__

class AccountAlreadyExistsError(Exception):
    pass

class BadCredentialsError(Exception):
    pass

class AccountFrame(PageFrame):
    def __init__(self, app, name):
        super(AccountFrame, self).__init__(app, name)

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
        super(AccountFrame, self).init()

        assert self.database_adapter is not None

    def process(self, session):
        account = session.page.get_account(session)

        if account is None:
            if session.page not in (self.login_page, self.create_page):
                return self.login_page.get_href(session)

class AccountView(Page):
    def get_title(self, session):
        return "Account"

    @xml
    def render_properties(self, session):
        account = self.get_account(session)

        props = (
            ("User name", xml_escape(account.name)),
            ("Last login", fmt_datetime(account.last_login)),
            ("Last logout", fmt_datetime(account.last_logout)),
        )

        return html_property_list(props)

    def render_account_name(self, session):
        account = self.get_account(session)
        return account.name

    def render_change_email_href(self, session):
        return self.frame.change_email_page.get_href(session)

    def render_change_password_href(self, session):
        return self.frame.change_password_page.get_href(session)

class AccountLogin(FormPage):
    def __init__(self, frame, name):
        super(AccountLogin, self).__init__(frame, name)

        self.name_input = StringInput(StringParameter(self, "name"))
        self.name_input.title = "User name"

        self.password_input = SecretInput(SecretParameter(self, "password"))
        self.password_input.title = "Password"

        self.exit_input.default_value = "/" # XXX

    def get_title(self, session):
        return "Log in"

    def process_continue(self, session):
        name = self.name_input.get(session)
        password = self.password_input.get(session)

        self.reset_client_session_id(session)

        try:
            account = self.frame.database_adapter.login(session, name, password)
        except BadCredentialsError:
            self.add_error(session, "Wrong user name or password")

        self.check_errors(session)

        self.set_account(session, account)

    def render_create_href(self, session):
        return self.frame.create_page.get_href(session)

class AccountLogout(FormPage):
    def get_title(self, session):
        return "Log out"

    def do_process(self, session):
        account = self.get_account(session)

        assert account is not None

        self.frame.database_adapter.logout(session, account)

        self.reset_client_session_id(session)
        self.set_account(session, None)

        self.set_result_message(session, "You are now logged out")

        return self.app.get_href(session)

class AccountCreate(FormPage):
    def __init__(self, frame, name):
        super(AccountCreate, self).__init__(frame, name)

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

    def get_title(self, session):
        return "Create account"

    def process_continue(self, session):
        name = self.name_input.get(session)
        email = self.email_input.get(session)
        confirm_email = self.confirm_email_input.get(session)
        password = self.password_input.get(session)
        confirm_password = self.confirm_password_input.get(session)

        if email != confirm_email:
            msg = "Confirmation email address does not match"
            self.confirm_email_input.add_error(session, msg)

        if password != confirm_password:
            msg = "Confirmation password does not match"
            self.confirm_password_input.add_error(session, msg)

        self.check_errors(session)

        try:
            account = self.frame.database_adapter.create \
                (session, name, email, password)
        except AccountAlreadyExistsError:
            msg = "An account with this name already exists"
            self.add_error(session, msg)

        self.check_errors(session)

        self.reset_client_session_id(session)
        self.set_account(session, account)

    def render_login_href(self, session):
        return self.frame.login_page.get_href(session)

class AccountChangeForm(FormPage):
    def __init__(self, frame, name):
        super(AccountChangeForm, self).__init__(frame, name)

        self.email_input = StringInput(StringParameter(self, "email"))
        self.email_input.title = "Email address"

        self.password_input = SecretInput(SecretParameter(self, "password"))
        self.password_input.title = "Password"

class AccountChangeEmail(AccountChangeForm):
    def __init__(self, frame, name):
        super(AccountChangeEmail, self).__init__(frame, name)

        self.email_input.title = "Current email address"

        self.new_email_input = StringInput(StringParameter(self, "new_email"))
        self.new_email_input.title = "New email address"

        self.confirm_new_email_input = StringInput \
            (StringParameter(self, "confirm_new_email"))
        self.confirm_new_email_input.title = "Confirm new email address"

    def get_title(self, session):
        return "Change email address"

    def process_continue(self, session):
        account = self.get_account(session)

        email = self.email_input.get(session)
        password = self.password_input.get(session)
        new_email = self.new_email_input.get(session)
        confirm_new_email = self.confirm_new_email_input.get(session)

        if new_email != confirm_new_email:
            msg = "Confirmation email address does not match"
            self.confirm_new_email_input.add_error(session, msg)

        self.check_errors(session)

        self.reset_client_session_id(session)

        try:
            self.frame.database_adapter.change_email \
                (session, account, email, password, new_email)
        except BadCredentialsError:
            self.add_error(session, "Wrong email or password")

        self.check_errors(session)

        self.set_result_message(session, "Email address changed")

class AccountChangePassword(AccountChangeForm):
    def __init__(self, frame, name):
        super(AccountChangePassword, self).__init__(frame, name)

        self.password_input.title = "Current password"

        self.new_password_input = SecretInput \
            (SecretParameter(self, "new_password"))
        self.new_password_input.title = "New password"

        self.confirm_password_input = SecretInput \
            (SecretParameter(self, "confirm_password"))
        self.confirm_password_input.title = "Confirm new password"

    def get_title(self, session):
        return "Change password"

    def process_continue(self, session):
        account = self.get_account(session)

        email = self.email_input.get(session)
        password = self.password_input.get(session)
        new_password = self.new_password_input.get(session)
        confirm_password = self.confirm_password_input.get(session)

        if new_password != confirm_password:
            msg = "Confirmation password does not match"
            self.confirm_password_input.add_error(session, msg)

        self.check_errors(session)

        self.reset_client_session_id(session)

        try:
            self.frame.database_adapter.change_password \
                (session, account, email, password, new_password)
        except BadCredentialsError:
            self.add_error(session, "Wrong email or password")

        self.check_errors(session)

        self.set_result_message(session, "Password changed")
