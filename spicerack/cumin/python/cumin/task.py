from rosemary.model import *
from wooly.forms import *
from wooly.resources import *
from wooly.widgets import *

from formats import *
from main import *
from parameters import *
from util import *

from wooly.widgets import Link

log = logging.getLogger("cumin.task")
strings = StringCatalog(__file__)

class Task(object):
    def __init__(self, app):
        self.app = app
        self.name = self.__class__.__name__
        self.form = None

        self.app.tasks.append(self)

    def init(self):
        log.info("Initializing %s", self)

        assert self.form, self
        self.app.form_page.modes.add_mode(self.form)
        
    def get_title(self, session, obj):
        pass

    def get_description(self, session, obj=None):
        return self.get_title(session, obj)

    def get_href(self, session, obj):
        return self.enter(session, obj).marshal()

    def enter(self, session, obj):
        form_session = wooly.Session(self.app.form_page)

        if obj:
            self.form.id.set(form_session, obj._id)

        self.form.return_url.set(form_session, session.marshal())
        self.form.show(form_session)

        self.do_enter(session, obj, form_session)

        return form_session

    def do_enter(self, session, obj, form_session):
        pass

    def exit(self, session, obj):
        log.debug("Exiting %s", self)

        url = self.form.return_url.get(session)
        osession = wooly.Session.unmarshal(self.app, url)

        self.do_exit(osession, obj)

        log.info("Exited %s", self)

        return osession

    def do_exit(self, session, obj):
        pass

    def exit_with_redirect(self, session, obj):
        osession = self.exit(session, obj)
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
            self.do_invoke(session, obj, invoc, *args, **kwargs)
        except Exception, e:
            self.exception(invoc, e)

    def do_invoke(self, session, obj, invoc, **kwargs):
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

class TaskInvocation(object):
    PENDING = "Pending"
    FAILED = "Failed"
    OK = "OK"

    def __init__(self, task, session):
        self.task = task

        session.add_notice(self)
        
        self.user = session.get_user()

        self.timestamp = datetime.now()

        self.start_time = None
        self.end_time = None
        self.update_time = None

        self.status = None
        self.exception = None
        self.description = None

        self.status_code = None
        self.output_args = None

        self.dismissed = False
        
    def __setattr__(self, name, value):
        if name in ("status"):
            self.timestamp = datetime.now()
        super(TaskInvocation, self).__setattr__(name, value)   

    def get_timestamp(self, session):
        if self.timestamp:
            return self.timestamp

    def get_description(self, session):
        if self.description:
            return self.description

        return self.task.get_description(session)

    def get_status(self, session):
        if self.exception:
            return "%s (%s)" % (self.status, str(self.exception))

        #return "%s: %s" % (self.status, str(self.output_args))
        if self.status is self.OK:
            if self.status_code:
                return self.status_code

        return self.status

    def get_message(self, session):
        timestamp = self.get_timestamp(session)
        description = xml_escape(self.get_description(session))
        if not description:
            description = ""
        status = xml_escape(str(self.get_status(session)))
        return "<span class='notification_time'>%s</span>  %s: %s" % ("%s-%02d-%02d %02d:%02d:%02d" % (timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute, timestamp.second), description, status)

    def end(self):
        log.debug("Ending %s", self.task)

        if self.status is self.PENDING:
            self.status = self.OK

        now = datetime.now()

        self.end_time = now
        self.update_time = now

        log.info("Ended %s", self.task)

    @classmethod
    def status_and_args(cls, *args):
        # This is a convenience function that can be
        # used to check results from a call when using
        # custom callbacks instead of completion() below...
        output_args = None
        if len(args) == 0:
            # We have to test this case now since we've made args
            # variable length.  Just call it OK
            status_code = TaskInvocation.OK

        elif len(args) == 1:
            # Status is ok if status_code is not an exception and result
            # goes in output_args
            status_code = args[0]
            if not isinstance(status_code, Exception):
                output_args = status_code
                status_code = TaskInvocation.OK
        else:
            status_code, output_args = args[0:2]
        return status_code, output_args

    @classmethod
    def is_success(cls, *args):
        s, a = TaskInvocation.status_and_args(*args)
        return s in (0, TaskInvocation.OK)

    def make_callback(self):
        def completion(*args):
            # Callback argument formats come in two basic flavors in Cumin
            # depending on the semantics of the async op:
            # callback(status, result)
            # callback(result) where type(result) == Exception indicates
            #   a failure status.
            # Allow this general mechanism to handle both types.
            status_code, output_args = self.status_and_args(*args)

            # Make results recorded directly through the callback
            # match what is done when TaskInvocation values are
            # set by an ObjectTask or Task on failure
            # (see Task.invoke() and Task.exception() above)
            # Previously the different mechanisms produced different results.
            if isinstance(status_code, Exception):
                self.status = self.FAILED
                self.exception = status_code
            else:
                self.status_code = status_code
                self.output_args = output_args
            self.end()
        return completion

class TaskLink(Link):
    def __init__(self, app, name, task, object=None):
        super(TaskLink, self).__init__(app, name)

        self.task = task
        self.object = object

    def render_href(self, session):
        obj = None

        if self.object:
            obj = self.object.get(session)

        return self.task.get_href(session, obj)

    def render_content(self, session):
        obj = None

        if self.object:
            obj = self.object.get(session)

        return self.task.get_title(session, obj)

class TaskButton(FormButton):
    def __init__(self, app, name, task, object=None):
        super(TaskButton, self).__init__(app, name)

        self.task = task
        self.object = object

    def process_submit(self, session):
        obj = None

        if self.object:
            obj = self.object.get(session)

        href = self.task.get_href(session, obj)
        self.page.redirect.set(session, href)

    def render_content(self, session):
        obj = None

        if self.object:
            obj = self.object.get(session)

        return self.task.get_title(session, obj)

class ObjectTaskForm(FoldingFieldSubmitForm):
    def __init__(self, app, name, task, cls):
        super(ObjectTaskForm, self).__init__(app, name)

        self.task = task
        self.cls = cls

        self.id = IntegerParameter(app, "id")
        self.add_parameter(self.id)

        self.object = ObjectAttribute(app, "object", self.cls, self.id)
        self.add_attribute(self.object)

    def do_process(self, session):
        self.object.process(session)

        super(ObjectTaskForm, self).do_process(session)

    def process_submit(self, session):
        self.validate(session)

        if not self.errors.get(session):
            obj = self.object.get(session)

            self.task.invoke(session, obj)
            self.task.exit_with_redirect(session)

    def render_title(self, session):
        obj = self.object.get(session)
        return self.task.get_title(session, obj)

    def render_content(self, session):
        if len(self.main_fields.fields):
            return super(ObjectTaskForm, self).render_content(session)

        obj = self.object.get(session)
        return obj.get_title()

# class SelectionTaskForm
