from qpid.connection import *
from qpid.util import *

from rosemary.model import *
from wooly.forms import *
from wooly.resources import *
from wooly.widgets import *

from formats import *
from main import *
from task import *
from util import *

from wooly.widgets import Link

log = logging.getLogger("cumin.objecttask")
strings = StringCatalog(__file__)

class ObjectTask(object):
    def __init__(self, app):
        self.app = app

        # XXX This is an unfortunate workaround for some broken
        # modeling of tasks (my work!)
        self.name = "%s_%i" % (self.__class__.__name__, id(self))

        self.form = None

    def init(self):
        log.info("Initializing %s", self)

    def get_title(self, session):
        pass

    def get_description(self, session):
        return self.get_title(session)

    def get_href(self, session):
        return self.enter(session).marshal()

    def enter(self, session):
        log.debug("Entering %s", self)

        return session

    def exit(self, session):
        log.debug("Exiting %s", self)

        url = self.form.return_url.get(session)
        osession = wooly.Session.unmarshal(self.app, url)

        self.do_exit(osession)

        log.info("Exited %s", self)

        return osession

    def do_exit(self, session):
        pass

    def exit_with_redirect(self, session):
        osession = self.exit(session)
        self.form.page.redirect.set(session, osession.marshal())

    def start(self, session, obj):
        log.debug("Starting %s", self)

        invoc = TaskInvocation(self, session)

        now = datetime.now()

        invoc.start_time = now
        invoc.update_time = now
        invoc.status = invoc.PENDING

        log.info("Started %s", self)

        return invoc

    def invoke(self, session, obj, *args, **kwargs):
        if obj:
            assert isinstance(obj, RosemaryObject), obj

        invoc = self.start(session, obj)

        try:
            self.do_invoke(invoc, obj, *args, **kwargs)
        except Exception, e:
            self.exception(invoc, e)

    def do_invoke(self, invoc, obj, *args, **kwargs):
        pass

    def exception(self, invoc, e):
        now = datetime.now()

        invoc.status = invoc.FAILED
        invoc.end_time = now
        invoc.update_time = now
        invoc.exception = e

        log.debug("Exception during task invocation", exc_info=True)

    def __str__(self):
        return "%s.%s" % (self.__module__, self.__class__.__name__)

class ObjectTaskLink(Link):
    def __init__(self, app, name, task):
        assert isinstance(task, ObjectTask), task

        super(ObjectTaskLink, self).__init__(app, name)

        self.task = task

class ObjectTaskButton(FormButton):
    def __init__(self, app, task):
        super(ObjectTaskButton, self).__init__(app, task.name)

        self.task = task

    def process_submit(self, session):
        href = self.task.get_href(session)
        self.page.redirect.set(session, href)

    def render_content(self, session):
        return self.task.get_title(session)
