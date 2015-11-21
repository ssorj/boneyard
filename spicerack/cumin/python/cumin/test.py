from parsley.test import *
from wooly import *

from user import *
from util import *

log = logging.getLogger("cumin.test")

class CuminTest(Test):
    def __init__(self, app):
        super(CuminTest, self).__init__("cumin", None)

        self.app = app
        self.user = None

    def init(self):
        for module in self.app.modules:
            module.init_test(self)

        super(CuminTest, self).init()

    def do_run(self, session):
        log.info("Waiting for the broker to connect")

        def connect():
            if self.app.model.mint.model.agents:
                log.info("The broker is connected")
                return True

        connected = retry(connect)

        if not connected:
            raise Exception("Failed to connect to broker")

        self.user = Subject.getByName("tester")

        if not self.user:
            self.user = Subject(name="tester", password="XXX")
            self.user.syncUpdate()

        super(CuminTest, self).do_run(session)

class TaskFormTest(Test):
    def __init__(self, name, parent, task):
        super(TaskFormTest, self).__init__(name, parent)

        self.task = task

    def enter(self, session, s):
        return self.task.enter(s, None)

    def add_input(self, session, s):
        pass

    def check(self, session, s):
        pass

    def do_run(self, session):
        s = MainPageSession(self.harness)

        s = self.enter(session, s)

        check_render(s)

        self.add_input(session, s)

        check_submit_form(s, self.task.form)

        self.check(session, s)

        super(TaskFormTest, self).do_run(session)
    
class MainPageSession(Session):
    def __init__(self, harness):
        super(MainPageSession, self).__init__(harness.test.app.main_page)

        usess = UserSession(harness.test.app, harness.test.user)
        self.user_session = usess

def retry(fn):
    result = None

    for i in range(10):
        result = fn()

        if result:
            break

        sleep(1)

    return result

def check_render(session):
    session.page.process(session)
    session.page.render(session)

def check_submit_form(session, form):
    form.submit(session)

    session.page.process(session)

    redirect = session.page.redirect.get(session)

    if redirect is None:
        errors = task.form.errors.get(ns)

        if errors:
            raise Exception("Unexpected form input errors")

    nsession = Session.unmarshal(session.page.app, redirect)

    check_render(nsession)

def check_get_object(cls, **criteria):
    def get():
        for obj in cls.selectBy(**criteria):
            return obj

    obj = retry(get)

    if not obj:
        args = (cls.__name__, criteria)
        raise Exception("Object %s(%s) not found" % args)

    return obj

def check_removed(cls, **criteria):
    def find():
        for obj in cls.selectBy(**criteria):
            return

        return True

    removed = retry(find)

    if not removed:
        args = (cls.__name__, criteria)
        raise Exception("Object %s(%s) not removed" % args)
