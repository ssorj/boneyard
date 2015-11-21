from cumin.main import CuminModule
from widgets import LoginPage, AccountPage

class Module(CuminModule):
    def __init__(self, app, name):
        super(Module, self).__init__(app, name)
        
        self.app.login_page = LoginPage(self.app, "login.html")
        self.app.add_page(self.app.login_page)

        self.app.account_page = AccountPage(self.app, "account.html")
        self.app.add_page(self.app.account_page, add_to_link_set=True)

        self.app.login_page.protected = False
        self.app.login_page.css_page.protected = False
        self.app.login_page.javascript_page.protected = False
