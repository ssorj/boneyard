from wooly import *
from wooly.resources import *
from wooly.widgets import *

from formats import *
from util import *
from widgets import *

log = logging.getLogger("cumin.objectframe")
strings = StringCatalog(__file__)

class ObjectFrame(Frame, ModeSet):
    def __init__(self, app, name, cls):
        super(ObjectFrame, self).__init__(app, name)

        self.cls = cls

        # This will hold the id of the object that should be assigned 
        # to self.object (it is the _id field from a sql table).
        # Both the id and the object are typically determined during
        # the "process" pass before a page is rendered.
        self.id = IntegerParameter(app, "id")
        self.add_parameter(self.id)

        # This will be given a value during the "process" pass after
        # self.id is determined (lookup by id)
        self.object = Attribute(app, "object")
        self.add_attribute(self.object)

        self.view = self.get_view(app, "view", self.object)
        #self.view = ObjectView(app, "view", self.object)
        self.add_child(self.view)

        self.icon_href = "resource?name=action-36.png"

        self.tasks = list()

        self.do_check_viewable = False

    def init(self):
        super(ObjectFrame, self).init()

        assert self.cls, self

        for task in self.tasks:
            task.init()

    def get_href(self, session, id):
        branch = session.branch()

        self.id.set(branch, id)
        self.view.show(branch)

        return branch.marshal()

    def get_title(self, session):
        obj = self.object.get(session)

        return "%s '%s'" % (obj._class._title, obj.get_title())

    def not_viewable_redirect(self):
        return (self.parent, 
                "Logged in user does not own a specified object")

    def check_owner(self, obj, session):
        return not hasattr(obj, "Owner") or \
            session.client_session.check_owner(obj.Owner)

    def check_viewable(self, obj, session):
        frame = None
        message = None
        okay = self.check_owner(obj, session)
        if not okay:
            frame, message = self.not_viewable_redirect()
        return okay, frame, message

    def do_process(self, session):
        # XXX don't process if this frame is invisible

        id = self.id.get(session)
        assert id

        obj = self.get_object(session, id)
        self.object.set(session, obj)

        # If the check is turned on, see if the object can be
        # viewed by the session.  The check_viewable method will
        # return a status, as well as a frame to redirect to and 
        # a message if the status is false
        okay = not self.do_check_viewable or obj is None
        if not okay:
            okay, frame, message = self.check_viewable(obj, session)
        if okay:
            super(ObjectFrame, self).do_process(session)
        else:
            self.set_redirect(session, frame, message)
 
    def _allow_none(self, session):
        try:
            return self.page.allow_object_not_found.get(session)
        except:
            pass
        return False

    def get_object(self, session, id):
        try:
            return self.cls.get_object_by_id(session.cursor, id)
        except:
            if self._allow_none(session):
                return None
            raise

    def get_view(self, app, name, obj):
        return ObjectView(app, name, obj)

class ObjectAttributes(Widget):
    def __init__(self, app, name, object):
        super(ObjectAttributes, self).__init__(app, name)

        self.object = object

        self.entry = ObjectAttributesEntry(app, "entry")
        self.add_child(self.entry)

    def get_attributes(self, session):
        return ()

    def render_attributes(self, session):
        writer = Writer()

        obj = self.object.get(session)

        for attr in self.get_attributes(session):
            # name and title are from rosemary xml files
            name = attr.title
            # We are going to escape the value in ObjectAttributesEntry below
            value = obj.get_formatted_value(attr.name, escape=False)
            title = attr.description

            writer.write(self.entry.render(session, name, value, title))
    
        return writer.to_string()

class ObjectAttributesEntry(Widget):
    def render_name(self, session, name, value, description):
        return name

    def render_value(self, session, name, value, description):
        if value is None:
            return fmt_none()

        if isinstance(value, str):
            value = self.break_up_long_lines(value)

        return xml_escape(str(value))

    def render_html_title(self, session, name, value, description):
        return description

    def break_up_long_lines(self, string):
        if " " in string[0:80]:
            return string

        lines = list()

        length = len(string)
        prev = 0

        for curr in range(80, length, 80):
            lines.append(string[prev:curr])
            prev = curr

        lines.append(string[prev:length])

        return " ".join(lines)

class ObjectTasks(Widget):
    def __init__(self, app, name, object):
        super(ObjectTasks, self).__init__(app, name)

        self.object = object

        self.link = ObjectTasksLink(app, "link")
        self.add_child(self.link)

        self.table_tmpl = WidgetTemplate(self, "table_html")

    def do_render(self, session):
        visible_tasks = [x for x in self.frame.tasks if x.visible]
        if len(visible_tasks) > 6:
            writer = Writer()
            self.table_tmpl.render(writer, session)
            return writer.to_string()
        else:
            return super(ObjectTasks, self).do_render(session)

    def render_links1(self, session):
        return self.render_task_links(session, 0)

    def render_links2(self, session):
        return self.render_task_links(session, 6)

    def render_task_links(self, session, start):
        writer = Writer()
        visible_tasks = [x for x in self.frame.tasks if x.visible]
        end = min(start + 6, len(visible_tasks))
        for task in visible_tasks[start:end]:
            writer.write(self.link.render(session, task))

        return writer.to_string()

    def render_links(self, session):
        return self.render_task_links(session, 0)

class ObjectTasksLink(Link):
    def render_href(self, session, task):
        return task.get_href(session)

    def render_content(self, session, task):
        return task.get_title(session)

class SummaryTasks(ObjectTasks):
    # don't ouput the html container if there will not be any
    # content since the container has margins
    def do_render(self, session):
        visible_tasks = [x for x in self.frame.tasks if x.visible]
        if len(visible_tasks):
            return super(SummaryTasks, self).do_render(session)

class ObjectView(Widget):
    def __init__(self, app, name, object):
        super(ObjectView, self).__init__(app, name)

        self.object = object

        self.context = ObjectViewContext(app, "context", self.object)
        self.add_child(self.context)

        self.heading = ObjectViewHeading(app, "heading", self.object)
        self.add_child(self.heading)

        self.summary = self.get_summary(app, "summary", self.object)
#        self.summary = ObjectViewSummary(app, "summary", self.object)
        self.add_child(self.summary)

        self.body = TabbedModeSet(app, "body")
        self.add_child(self.body)

    def init(self):
        self.add_details_tab()

        super(ObjectView, self).init()

    def add_details_tab(self):
        """ allow derived views to skip adding details tab """
        self.add_tab(ObjectDetails(self.app, "details", self.object))

    def add_tab(self, widget):
        self.body.add_tab(widget)

    def render_title(self, session):
        obj = self.object.get(session)
        title = ""
        if obj is not None:        
            title = obj.get_title()
        else:
            # useful in the case where we are dealing with 
            # non-database objects and the object title is passed in as the id
            title = self.frame.id.get(session)
        return title

    def get_summary(self, app, name, obj):
        return ObjectViewSummary(app, name, obj)    

class ObjectViewChild(Widget):
    def __init__(self, app, name, object):
        super(ObjectViewChild, self).__init__(app, name)

        self.object = object

class ObjectViewContext(ObjectViewChild):
    def __init__(self, app, name, object):
        super(ObjectViewContext, self).__init__(app, name, object)

        self.link = ObjectViewContextLink(app, "link")
        self.add_child(self.link)

    def render_links(self, session):
        links = list()

        for frame in self.parent.ancestors:
            if not isinstance(frame, Frame):
                break

            links.append(self.link.render(session, frame))

        trimmed_links = list()
        text_matcher = re.compile('<a.*?>(.*?)</a>')
        for onelink in links:
            new_link = onelink
            #get just the text that we will be displaying to truncate
            result = text_matcher.search(onelink)                
            if(result.group(1) and len(result.group(1)) > 100):
                origText = result.group(1)
                newText = result.group(1)[:100] + "...'"
                new_link = onelink.replace(origText, newText, 1)
            trimmed_links.append(new_link)
                                     
        return " &rsaquo; ".join(reversed(trimmed_links))
    
class ObjectViewContextLink(Link):
    def __init__(self, app, name):
        super(ObjectViewContextLink, self).__init__(app, name)

    def edit_session(self, session, frame):
        frame.view.show(session)

    def render_class(self, session, frame):
        cls = super(ObjectViewContextLink, self).render_class(session)

        if self.frame is frame:
            cls = "%s selected" % cls

        return cls

    def render_content(self, session, frame):
        return xml_escape(frame.get_title(session))

class ObjectViewHeading(ObjectViewChild):
    def __init__(self, app, name, object):
        super(ObjectViewHeading, self).__init__(app, name, object)

    def render_icon_href(self, session):
        return self.frame.icon_href

    def render_title(self, session):
        retval = self.parent.render_title(session)
        if retval is not None and isinstance(retval, str) and len(retval) > 100:
            retval = retval[:100] + "..."
        return xml_escape(retval)
    
class ObjectViewSummary(ObjectViewChild):
    def __init__(self, app, name, object):
        super(ObjectViewSummary, self).__init__(app, name, object)

        tasks = SummaryTasks(app, "tasks", self.object)
        self.add_child(tasks)

        self.auxlink = None

    def render_wide(self, session):
        visible_tasks = [x for x in self.frame.tasks if x.visible]
        if len(visible_tasks) > 6:
            return "wide"

    def render_auxlink(self, session):
        pass

    def render_auxtitle(self, session):
        pass

class DetailsAttributes(ObjectAttributes):
    pass

class ObjectDetails(Widget):
    def __init__(self, app, name, object):
        super(ObjectDetails, self).__init__(app, name)

        self.object = object

        attrs = self.Headers(app, "headers", self.object)
        attrs.update_enabled = True
        self.add_child(attrs)

        attrs = self.References(app, "refs", self.object)
        attrs.update_enabled = True
        self.add_child(attrs)

        attrs = self.Properties(app, "props", self.object)
        attrs.update_enabled = True
        self.add_child(attrs)

        attrs = self.Statistics(app, "stats", self.object)
        attrs.update_enabled = True
        self.add_child(attrs)
        
        self.main_tmpl = WidgetTemplate(self, "html")

    def render_title(self, session):
        return "Details"

    class Headers(DetailsAttributes):
        def get_attributes(self, session):
            obj = self.object.get(session)
            return obj._class._headers

        def render_title(self, session):
            return "QMF Headers"

    class References(DetailsAttributes):
        def get_attributes(self, session):
            obj = self.object.get(session)
            return obj._class._references

        def render_title(self, session):
            return "References"

    class Properties(DetailsAttributes):
        def get_attributes(self, session):
            obj = self.object.get(session)
            return obj._class._properties

        def render_title(self, session):
            return "Properties"

    class Statistics(DetailsAttributes):
        def get_attributes(self, session):
            obj = self.object.get(session)
            return obj._class._statistics

        def render_title(self, session):
            return "Statistics"
        
    def do_render(self, session, *args):
        # necessary so that we will get proper rendering of the details tab
        if self.defer_enabled and not getattr(session, "background", None):
            writer = Writer()
            self.__defer_tmpl.render(writer, session, *args)
            return writer.to_string()
        else:
            writer = Writer()
            # if we have an object, we're in good shape
            # otherwise, show the "no content" template
            if self.frame.object.get(session):
                self.main_tmpl.render(writer, session, *args)
            else:
                self.nocontent_tmpl.render(writer, session, *args)
            return writer.to_string()           

class ObjectFrameTask(ObjectTask):
    def __init__(self, app, frame):
        super(ObjectFrameTask, self).__init__(app)

        self.frame = frame
        self.frame.tasks.append(self)

        # should this task be listed in the ObjectViewSummary section
        self.visible = True

    def init(self):
        super(ObjectFrameTask, self).init()

        if not self.form:
            self.form = ObjectFrameTaskForm(self.app, self.name, self)
            self.form.init()

    def enter(self, session):
        id = self.frame.id.get(session)

        nsession = wooly.Session(self.app.form_page)

        self.form.id.set(nsession, id)
        self.form.return_url.set(nsession, session.marshal())
        self.form.show(nsession)

        self.do_enter(nsession, session)

        return nsession

    def do_enter(self, session, osession):
        pass

class ObjectFrameTaskForm(FoldingFieldSubmitForm):
    def __init__(self, app, name, task):
        super(ObjectFrameTaskForm, self).__init__(app, name)

        self.task = task

        self.id = IntegerParameter(app, "id")
        self.add_parameter(self.id)

        self.object = SessionAttribute(self, "object")

        self.app.form_page.modes.add_mode(self)

    def do_process(self, session):
        id = self.id.get(session)

        if id:
            # XXX don't love this; impl get_object on OTForm instead
            obj = self.task.frame.get_object(session, id)
            self.object.set(session, obj)

        super(ObjectFrameTaskForm, self).do_process(session)

    def process_submit(self, session):
        obj = self.object.get(session)

        self.task.invoke(session, obj)
        self.task.exit_with_redirect(session)

    def render_title(self, session):
        return self.task.get_title(session)

    def render_content(self, session):
        if len(self.main_fields.fields):
            return super(ObjectFrameTaskForm, self).render_content(session)

        obj = self.object.get(session)
        return xml_escape(obj.get_title())

class ObjectFrameTaskFeedbackForm(ObjectFrameTaskForm):
    # substitute our submit button because it has feedback when it is clicked
    def create_submit(self, app):
        self.submit_button = self.SubmitFeedbackButton(self.app, "submit")
        self.submit_button.tab_index = 201
        self.add_button(self.submit_button)

    class SubmitFeedbackButton(FormButton):
        def render_class(self, session):
            return "submit"

        def render_content(self, session):
            return self.parent.render_submit_content(session)

        def render_onclick(self, session):
            return "feedback_click_button"
