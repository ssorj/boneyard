from forms import *
from pages import HtmlPage
from server import WebServer
from util import *
from widgets import *
from wooly import Application

strings = StringCatalog(__file__)

class DemoServer(WebServer):
    def authorized(self, session):
        return True

class DemoApplication(Application):
    def __init__(self):
        super(DemoApplication, self).__init__()

        self.model = DemoModel(self)

        self.main_page = DemoPage(self, "index")
        self.add_page(self.main_page)
        self.set_default_page(self.main_page)

        hdef = os.path.normpath("/usr/share/wooly")
        self.home = os.environ.get("WOOLY_DEMO_HOME", hdef)

        self.add_resource_dir(os.path.join(self.home, "resources"))

        self.debug = True

    def start(self):
        self.model.start()

    def stop(self):
        self.model.stop()

class DemoModel(object):
    def __init__(self, app):
        super(DemoModel, self).__init__()

        self.app = app
        self.incrementing_counter = 0

        self.update_thread = self.UpdateThread(self)

    def start(self):
        self.update_thread.start()

    def stop(self):
        pass

    class UpdateThread(Thread):
        def __init__(self, model):
            super(DemoModel.UpdateThread, self).__init__()

            self.model = model
            self.setDaemon(True)

        def run(self):
            while True:
                time.sleep(1)

                self.model.incrementing_counter += 1

class DemoPage(HtmlPage):
    def __init__(self, app, name):
        super(DemoPage, self).__init__(app, name)

        self.main_view = MainView(app, "main")
        self.add_child(self.main_view)

class MainView(Widget):
    def __init__(self, app, name):
        super(MainView, self).__init__(app, name)

        tabs = TabSet(app, "tabs")
        self.add_child(tabs)

        #self.intro_tab = Introduction(app, "intro")
        #tabs.add_tab(self.intro_tab)

        #self.link_tab = LinkDemo(app, "link")
        #tabs.add_tab(self.link_tab)

        #self.form_tab = FormDemo(app, "form")
        #tabs.add_tab(self.form_tab)

class Introduction(Widget):
    def get_title(self, session):
        return "Introduction"

class LinkDemo(Widget):
    def __init__(self, app, name):
        super(LinkDemo, self).__init__(app, name)

        self.visit_intro_link = self.VisitIntroLink(app, "visit_intro_link")
        self.add_child(self.visit_intro_link)

        self.secret_toggle = self.SecretToggle(app, "secret_toggle")
        self.add_child(self.secret_toggle)

    def get_title(self, session):
        return "Links"

    def render_secret(self, session):
        if self.secret_toggle.is_enabled(session):
            return "Above all things, I love persimmons."

    class VisitIntroLink(Link):
        def render_href(self, session):
            branch = session.branch()
            self.app.main_page.main_view.intro_tab.show(branch)
            return branch.marshal()

        def render_content(self, session):
            return "See the Egress!"

    class SecretToggle(Toggle):
        def render_content(self, session):
            if self.is_enabled(session):
                return "Hide that secret"
            else:
                return "Show me a secret"

class FormDemo(Widget):
    def __init__(self, app, name):
        super(FormDemo, self).__init__(app, name)

        self.address_form = self.AddressForm(app, "address")
        self.add_child(self.address_form)

        self.three_form = self.ThreeForm(app, "threeform")
        self.add_child(self.three_form)

    def get_title(self, session):
        return "Forms"

    class AddressForm(FieldSubmitForm):
        def __init__(self, app, name):
            super(FormDemo.AddressForm, self).__init__(app, name)

            self.name_ = self.Name(app, "first")
            self.add_field(self.name_)

            self.line_1 = self.Line1(app, "line1")
            self.add_field(self.line_1)

            self.line_2 = self.Line2(app, "line2")
            self.add_field(self.line_2)

        def get_title(self, session):
            return "Enter your address"

        class Name(StringField):
            def get_title(self, session):
                return "Name"

        class Line1(StringField):
            def get_title(self, session):
                return "Address Line 1"

        class Line2(StringField):
            def get_title(self, session):
                return "Address Line 2"

    class ThreeForm(ModeSet, Frame):
        def __init__(self, app, name):
            super(FormDemo.ThreeForm, self).__init__(app, name)

            self.one = self.One(app, "one")
            self.add_mode(self.one)

            self.two = self.Two(app, "two")
            self.add_mode(self.two)

            self.three = self.Three(app, "three")
            self.add_mode(self.three)

        class One(FieldSubmitForm):
            def __init__(self, app, name):
                super(FormDemo.ThreeForm.One, self).__init__(app, name)

                field = self.OneField(app, "first")
                self.add_field(field)

            def process_cancel(self, session):
                self.parent.three.show(session)

            def process_submit(self, session):
                self.parent.two.show(session)

            def get_title(self, session):
                return "Step 1"

            class OneField(StringField):
                def get_title(self, session):
                    return "Alpha"

        class Two(FieldSubmitForm):
            def __init__(self, app, name):
                super(FormDemo.ThreeForm.Two, self).__init__(app, name)

                field = self.TwoField(app, "second")
                self.add_field(field)

            def process_cancel(self, session):
                self.parent.one.show(session)

            def process_submit(self, session):
                self.parent.three.show(session)

            def get_title(self, session):
                return "Step 2"

            class TwoField(StringField):
                def get_title(self, session):
                    return "Beta"

        class Three(SubmitForm):
            def __init__(self, app, name):
                super(FormDemo.ThreeForm.Three, self).__init__(app, name)

            def process_cancel(self, session):
                self.parent.two.show(session)

            def process_submit(self, session):
                self.parent.one.show(session)

            def get_title(self, session):
                return "Step 3"

            def render_content(self, session):
                return "All done!"
