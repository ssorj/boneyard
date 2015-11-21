import subprocess

from wooly import *
from wooly.widgets import *
from wooly.resources import *

from cumin import *
from cumin.objecttask import *
from cumin.widgets import *
from cumin.util import *

import main

from wooly import Session

log = logging.getLogger("cumin.account.widgets")

strings = StringCatalog(__file__)

class AccountPage(CuminPage, ModeSet):
    def __init__(self, app, name):
        super(AccountPage, self).__init__(app, name)

        self.account = AccountMainView(app, "account")
        self.add_mode(self.account)
        self.set_default_frame(self.account)

    def render_title(self, session):
        return "Your Account"

class AccountMainView(CuminMainView):
    def __init__(self, app, name):
        super(AccountMainView, self).__init__(app, name)

        self.settings = SettingsFrame(app, "main")
        self.add_tab(self.settings)
        
class SettingsFrame(Frame):
    def __init__(self, app, name):
        super(SettingsFrame, self).__init__(app, name)

        self.change_password_form = ChangePasswordForm(app, "change_password")
        self.app.form_page.modes.add_mode(self.change_password_form)

        link = self.ChangePasswordLink(app, "change_password")
        self.add_child(link)

    def render_title(self, session):
        return "Settings"

    class ChangePasswordLink(Link):
        def render_href(self, session):
            nsession = wooly.Session(self.app.form_page)
            form = self.frame.change_password_form
            
            form.return_url.set(nsession, session.marshal())
            form.show(nsession)

            return nsession.marshal()

        def render_content(self, sessino):
            return "Change password"

class LoginPage(HtmlPage):
    def __init__(self, app, name):
        super(LoginPage, self).__init__(app, name)

        self.html_class = LoginPage.__name__

        self.logout = BooleanParameter(app, "logout")
        self.add_parameter(self.logout)

        self.origin = self.Origin(app, "origin")
        self.add_parameter(self.origin)

        form = LoginForm(app, "form")
        self.add_child(form)

        # Make sure that we don't force a user to 
        # be logged in when visiting the login page!
        self.check_login = False

    def do_process(self, session):
        if self.logout.get(session):
            try:
                del session.client_session.attributes["login_session"]
                session.client_session.reset_csrf()
            except KeyError:
                pass

        super(LoginPage, self).do_process(session)

    def render_title(self, session):
        return "Log In"

    class Origin(Parameter):
        def get_default(self, session):
            return Session(self.app.main_page).marshal()

class LoginForm(Form):
    def __init__(self, app, name):
        super(LoginForm, self).__init__(app, name)

        self.login_invalid = Attribute(app, "login_invalid")
        self.add_attribute(self.login_invalid)

        self.user_name = StringInput(app, "user_name")
        self.user_name.size = 20
        self.add_child(self.user_name)

        self.password = PasswordInput(app, "password")
        self.password.size = 20
        self.add_child(self.password)

        self.submit = self.Submit(app, "submit")
        self.add_child(self.submit)

    def do_process(self, session):
        if self.submit.get(session):
            name = self.user_name.get(session)
            password = self.password.get(session)

            self.validate(session)

            if not self.errors.get(session):
                user, ok = self.app.authenticator.authenticate(name, password)
                if ok:
                    # You're in! almost...
                    # Check for a valid group if group authorization is on
                    roles = []
                    if self.app.authorizator.is_enforcing():
                        if user is None:
                            # This was an external user with no role
                            # entry in the Cumin database.  We default the
                            # role to 'user'.  In the future we may store
                            # roles externally as well.
                            roles = ['user']
                        else:
                            cursor = self.app.database.get_read_cursor()
                            roles = self.app.admin.get_roles_for_user(
                                                                 cursor, user)
                        ok = self.app.authorizator.contains_valid_group(roles)
                        if not ok:
                            self.login_invalid.set(session, "roles")

                    # If we're still okay, set up the login
                    if ok:
                        if user is None:
                            user = name
                        login = LoginSession(self.app, user, roles)
                        
                        # We want to generate a new session id and record the
                        # login while keeping the rest of the session data.  
                        # This is to protect against session fixation attacks.
                        self.app.server.reset_client_session_id(session, login)

                        url = self.page.origin.get(session)
                        self.page.redirect.set(session, url)
                else:
                    self.login_invalid.set(session, "credentials")

    def render_operator_link(self, session):
        email = self.app.operator_email

        if email:
            return "<a href=\"mailto:%s\">site operator</a>" % email
        else:
            return "site operator"

    def render_login_invalid(self, session):
        reason = self.login_invalid.get(session)
        if reason == "roles":
            return self.get_string("roles_invalid")
        elif reason == "credentials":
            return self.get_string("login_invalid")

    class Submit(FormButton):
        def render_content(self, session):
            return "Submit"

class ChangePasswordForm(FoldingFieldSubmitForm):
    def __init__(self, app, name):
        super(ChangePasswordForm, self).__init__(app, name)

        self.current = self.Current(app, "current")
        self.current.required = True
        self.current.input.size = 20
        self.add_field(self.current)

        self.new0 = self.New0(app, "new0")
        self.new0.required = True
        self.new0.input.size = 20
        self.add_field(self.new0)

        self.new1 = self.New1(app, "new1")
        self.new1.required = True
        self.new1.input.size = 20
        self.add_field(self.new1)

    def validate(self, session):
        user = session.client_session.attributes["login_session"].user
        # In case a different login session for this user has made
        # changes, refresh the user object
        if hasattr(user, "load"):
            user.load(session.cursor)
        
        new0 = self.new0.get(session)
        new1 = self.new1.get(session)

        if new0 != new1:
            error = FormError("The new passwords do not match")
            self.errors.add(session, error)
            return 

        super(ChangePasswordForm, self).validate(session)

        # authenticator.update_password does authentication
        # before allowing the password change, no need to authenticate here

    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            newpassword = self.new0.get(session)
            oldpassword = self.current.get(session)
            user = session.client_session.attributes["login_session"].user
            try:
                status, message = self.app.authenticator.update_password(user.name, 
                                                                         oldpassword, 
                                                                         newpassword)
                if not status:
                    if not message:
                        message = "Update failed."
                    error = FormError(message)
                    self.errors.add(session, error)

            except Exception,e:
                log.debug("Error in external authenticator: %s" , e )
                error = FormError("Password change error. Please contact your site administrator.")
                self.errors.add(session,error)

        if not self.errors.get(session):
            # Just use a notice here to spoof a task completion.
            session.add_notice(Notice(preamble="Password changed", 
                                      message="OK",
                                      capitalize=False))
            url = self.return_url.get(session)
            self.page.redirect.set(session, url)

    def render_title(self, session):
        return "Change password"

    class Current(PasswordField):
        def render_title(self, session):
            return "Current password"

    class New0(PasswordField):
        def render_title(self, session):
            return "New password"

    class New1(PasswordField):
        def render_title(self, session):
            return "Repeat new password"
