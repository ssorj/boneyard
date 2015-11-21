from wooly import *
from wooly.pages import *
from wooly.datatable import *
from wooly.widgets import *
from wooly.forms import *
from wooly.sql import *
from wooly.tables import *

from objecttask import *
from objectselector import *
from parameters import *
from widgets import *
from formats import *
from task import *
from user import *
from util import *
import time

from wooly import Session
from wooly.widgets import Link
from wooly.tables import SqlTable
from cumin.objectframe import ObjectFrameTask

strings = StringCatalog(__file__)

class CuminSqlDataSet(SqlDataSet):
    def get_connection(self, session):
        return self.app.database.get_read_connection()

class CuminHeartBeat(Widget):
    """ the intent is to add stuff here """
    pass

class CuminMainView(TabbedModeSet):
    def __init__(self, app, name):
        super(CuminMainView, self).__init__(app, name)

        self.notifications = NotificationSet(app, "notifications")
        self.add_child(self.notifications)

        self.heartbeat = CuminHeartBeat(app, "heartbeat")
        self.add_child(self.heartbeat)

        self.links = CuminPageLinks(app, "links")
        self.add_child(self.links)

    def do_process(self, session, *args):
        self.notifications.process(session)
        self.heartbeat.process(session)
        self.links.process(session)

        super(CuminMainView, self).do_process(session, *args)

    def show_child(self, session, child):
        super(CuminMainView, self).show_child(session, child)

        frame = self.page.get_frame(session)

        if child not in frame.ancestors:
            self.page.set_frame(session, child)

    def render_user_name(self, session):
        login = session.client_session.attributes["login_session"]
        return xml_escape(login.user.name)

    def render_logout_href(self, session):
        page = self.app.login_page

        lsess = Session(page)

        page.logout.set(lsess, True)
        page.origin.set(lsess, session.marshal())

        return lsess.marshal()

    def render_tab_href(self, session, tab):
        if hasattr(tab, "top_tab"):
            branch = session.branch()
            tab.mode.set(branch, None)
            tab.show(branch)
            return branch.marshal()
        else:
            return super(CuminMainView, self).render_tab_href(session, tab)

    def render_about_href(self, session):
        page = self.app.about_page
        lsess = Session(page)
        return lsess.marshal()

class CuminPageLinks(ItemSet):
    def __init__(self, app, name):
        super(CuminPageLinks, self).__init__(app, name)
        self.app = app
        self.html_class = CuminPageLinks.__name__

    def do_get_items(self, session):
        return self.app.page_links

    def render_item_content(self, session, page):
        href = Session(page).marshal()
        title = page.render_title(session)
        if self.app.authorize_cb(session, page):
            return fmt_link(href, title)

    def render_item_class(self, session, page):
        if page is session.page:
            return "selected"
        else:
            return "_"

class CuminFrame(Frame, ModeSet):
    def __init__(self, app, name):
        super(CuminFrame, self).__init__(app, name)

        self.object = None

        self.__view = None
        self.__add = None
        self.__edit = None
        self.__remove = None

        self.top_tab = True

    def init(self):
        super(CuminFrame, self).init()

    def show_object(self, session, object):
        if self.object:
            self.object.set(session, object)

        if hasattr(self, "view"):
            self.view.show(session)

        return self

    def get_object(self, session):
        if self.object:
            return self.object.get(session)

    def set_object(self, session, object):
        return self.object.set(session, object)

    def get_href(self, session, object):
        branch = session.branch()
        self.show_object(branch, object)
        return branch.marshal()

    def add_sticky_view(self, frame):
        self.sticky_view = frame.view
        frame.view.sticky_frame = self

    def render_href(self, session, *args):
        branch = session.branch()
        if hasattr(self, "view"):
            self.view.show(branch)

        return branch.marshal()

    def render_title(self, session, *args):
        obj = self.get_object(session)
        cls = self.app.model.get_class_by_object(obj)

        if cls:
            return cls.get_object_title(session, obj)

    # XXX
    def get_title(self, session):
        return self.render_title(session)

class BackgroundInclude(Widget):
    def __init__(self, app, name):
        super(BackgroundInclude, self).__init__(app, name)

        self.data = None
        self.type = None

    def render_data(self, session):
        return self.data

    def render_background(self, session):
        data = self.render_data(session)
        sep = (data and "?" in data) and ";" or "?"
        return "%sformBackground=1" % sep

    def render_type(self, session):
        return self.type

class CuminTaskForm(SubmitForm, Frame):
    def __init__(self, app, name, task):
        super(CuminTaskForm, self).__init__(app, name)

        self.task = task
        self.object = None

    def init(self):
        super(CuminTaskForm, self).init()

        assert isinstance(self.object, Parameter)

    def process_submit(self, session):
        obj = self.object.get(session)

        self.task.invoke(session, obj)
        self.task.exit_with_redirect(session)

    def render_submit_content(self, session):
        return self.task.get_title(session)

    def render_title(self, session):
        return "Confirm"

    def render_content(self, session):
        obj = self.object.get(session)
        return "%s?" % self.task.get_description(session, obj)

class FormHelp(Widget):
    def __init__(self, app, name):
        super(FormHelp, self).__init__(app, name)

class CuminForm(SubmitForm):
    def __init__(self, app, name):
        super(CuminForm, self).__init__(app, name)

        self.help = self.Help(app, "help")
        self.add_child(self.help)

    def get_modal(self, session):
        return True

    def render_form_error(self, session, *args):
        pass

    class Help(FormHelp):
        def render_help_href(self, session, *args):
            return "resource?name=help.html#%s" % self.path

class EditablePropertyRenderer(TemplateRenderer, Widget):
    """Display input fields for editing properties

    Parent class needs to override do_get_items() and return a list of items.
    Each item should be a dictionary.
            ["name"] is required and should be the display label
            ["value"] is required and should be the value to edit
            ["type"] is required and should be an input type <"number" | "string">
            ["path"] is required and should be the DictParameter path to prepend to the name
            ["error"] is optional and should be the error text to display for that item
            ["property"] is optional and should be a dictionary of item properties
            ["orig"] is optional and should be the original value of the item before user edits
    """
    def __init__(self, widget, template_key):
        super(EditablePropertyRenderer, self).__init__(widget, template_key)

        self.__bool_template = WidgetTemplate(self, "bool_html")
        self.__string_template = WidgetTemplate(self, "string_html")
        self.__bigstring_template = WidgetTemplate(self, "bigstring_html")
        self.__number_template = WidgetTemplate(self, "number_html")
        self.__readonly_template = WidgetTemplate(self, "readonly_html")
        self.__orig_template = WidgetTemplate(self, "orig_html")

    def render_title(self, session, item):
        title = item["name"]
        if "property" in item:
            property = item["property"]
            if property.title:
                title = property.get_title(session)
        return escape_amp(title)

    def render_value(self, session, item):
        value = item["value"]
        type = item["type"]
        writable = True
        property = "property" in item and item["property"] or None
        if property:
            writable = property.writable

        writer = Writer()
        if not writable:
            self.__readonly_template.render(writer, session, item)
        elif type == "float" or type == "integer":
            self.__number_template.render(writer, session, item)
        else:
            # It's either a string or an expression, and the type value
            # will be recorded in the "type" hidden input for the element.
            # On processing, the type can be checked to deal with string
            # vs expression.
            if len(value) > 40:
                self.__bigstring_template.render(writer, session, item)
            else:
                self.__string_template.render(writer, session, item)

        return writer.to_string()

    def render_pname(self, session, item):
        return DictParameter.sep().join(
                (item["path"], escape_entity(item["name"]), "value"))

    def render_ptype_name(self, session, item):
        return DictParameter.sep().join(
                (item["path"], escape_entity(item["name"]), "type"))

    def render_ptype_value(self, session, item):
        return item["type"]

    def render_orig_value(self, session, item):
        if "orig" in item:
            writer = Writer()
            self.__orig_template.render(writer, session, item)
            return writer.to_string()

    def render_porig_name(self, session, item):
        return DictParameter.sep().join(
            (item["path"], escape_entity(item["name"]), "orig"))

    def render_porig_value(self, session, item):
        value = item["orig"]
        return escape_entity(str(value))

    def render_val(self, session, item):
        value = self.get_val(session, item)
        return escape_entity(str(value))

    def render_display_val(self, session, item):
        value = self.get_val(session, item)
        property = "property" in item and item["property"] or None
        if property:
            renderer = property.renderer
            if renderer:
                value = renderer(session, value)

        return escape_entity(str(value))

    def get_val(self, session, item):
        try:
            value = item["value"]
        except KeyError:
            value = ""
        return value

    def render_error(self, session, item):
        if "error" in item:
            return "<div class=\"error\">%s</div>" % item["error"]

    def render_inline_help(self, session, item):
        property = "property" in item and item["property"] or None
        if property:
            if property.example:
                example = "<span class=\"prop_example\">%s</span>" % property.example
            else:
                example = ""
            description = property.description or ""
            return " ".join((description, example))

    def render_false_selected(self, session, item):
        return item["value"].upper() == "FALSE" and "checked=\"checked\"" or ""

    def render_true_selected(self, session, item):
        return item["value"].upper() == "TRUE" and "checked=\"checked\"" or ""

    def render_edit_number_class(self, session, item):
        return "error" in item and "numeric_error" or "edit_number"

class CuminProperties(PropertySet):
    def __init__(self, app, name, object):
        super(CuminProperties, self).__init__(app, name)

        self.object = object

    def do_get_items(self, session):
        obj = self.object.get(session)
        cls = self.app.model.get_class_by_object(obj)

        return [(x.get_title(session), x.value(session, obj), x.escape)
                for x in cls.properties]

class CuminTasks(ActionSet):
    def __init__(self, app, name, object):
        super(CuminTasks, self).__init__(app, name)

        self.object = object

    def do_get_items(self, session):
        obj = self.object.get(session)
        cls = self.app.model.get_class_by_object(obj)

        return [(x.get_href(session, obj), x.get_title(session), True)
                for x in cls.tasks if x.navigable and not x.aggregate]

class CuminDetails(Widget):
    def __init__(self, app, name, object):
        super(CuminDetails, self).__init__(app, name)

        self.add_child(CuminProperties(app, "properties", object))
        self.add_child(CuminTasks(app, "tasks", object))

    def render_title(self, session):
        return "Details"

class CuminHeading(Widget):
    def render_title(self, session, *args):
        pass

    def render_icon_href(self, session, *args):
        return "resource?name=action-36.png"

class StateSwitch(ItemSet):
    def __init__(self, app, name):
        super(StateSwitch, self).__init__(app, name)

        self.param = Parameter(app, "param")
        self.add_parameter(self.param)

        self.__states = list()
        self.__titles = dict()
        self.__hover = dict()
        self.__bookmark = dict()

    def add_state(self, state, title, hover="", bm=None):
        self.__states.append(state)
        self.__titles[state] = title
        self.__hover[state] = hover
        self.__bookmark[state] = bm

        if self.param.default is None:
            self.param.default = state

    def get(self, session):
        return self.param.get(session)

    def set(self, session, value):
        return self.param.set(session, value)

    def get_items(self, session):
        return self.__states

    def get_title(self, state):
        return state in self.__titles and self.__titles[state]

    def get_hover(self, state):
        return state in self.__hover and self.__hover[state]

    def get_bookmark(self, state):
        return state in self.__bookmark and self.__bookmark[state]

    def get_click(self, session, state):
        return ""

    def get_attributes(self, state):
        return dict()

    def get_param_id(self):
        """ needed because the SubmitSwitch class uses
            a hidden input to set the param value instead
            of a link name/value pair """
        return self.param.path

    def render_item_link(self, session, state):
        branch = session.branch()
        self.set(branch, state)

        title = self.get_title(state)
        hover = self.get_hover(state)
        class_ = self.get(session) == state and "selected"
        bm = self.get_bookmark(state)
        click = self.get_click(session, state)
        attribs = self.get_attributes(state)

        return fmt_link(branch.marshal(), title, class_, link_title=hover, bm=bm, click=click, attribs=attribs)

class DynamicSwitch(StateSwitch):
    """ Used when the states are not fixed. 
    They vary each request """

    def __init__(self, app, name):
        super(DynamicSwitch, self).__init__(app, name)

        self.states = self.StatesAttribute(app, "states")
        self.add_attribute(self.states)

    def add_state(self, session, state, title, hover=""):
        state_attrib = self.states.get(session)
        state_attrib['states'].append(state)
        state_attrib['titles'][state] = title
        state_attrib['hover'][state] = hover

        if self.param.default is None:
            self.param.default = state

    def get_items(self, session):
        state_attrib = self.states.get(session)
        return state_attrib['states']

    def get_title(self, session, state):
        state_attrib = self.states.get(session)
        return state in state_attrib['titles'] and state_attrib['titles'][state]

    def get_hover(self, session, state):
        state_attrib = self.states.get(session)
        return state in state_attrib['hover'] and state_attrib['hover'][state]

    def get_bookmark(self, session, state):
        state_attrib = self.states.get(session)
        return state in state_attrib['bookmark'] and state_attrib['bookmark'][state]

    def get_click(self, session, state):
        return ""

    def get_attributes(self, session, state):
        return dict()

    def render_item_link(self, session, state):
        branch = session.branch()
        self.set(branch, state)

        title = self.get_title(session, state)
        hover = self.get_hover(session, state)
        class_ = self.get(session) == state and "selected"
        bm = self.get_bookmark(session, state)
        click = self.get_click(session, state)
        attribs = self.get_attributes(session, state)

        return fmt_link(branch.marshal(), title, class_, link_title=hover, bm=bm, click=click, attribs=attribs)

    class StatesAttribute(Attribute):
        def get_default(self, session):
            return {'states': [],
                    'titles': {},
                    'hover': {},
                    'bookmark': {}}

class GroupSwitch(StateSwitch):
    def __init__(self, app, name):
        super(GroupSwitch, self).__init__(app, name)

        self.add_state("j", "Jobs")
        self.add_state("g", "Groups")

class UnitSwitch(StateSwitch):
    def __init__(self, app, name):
        super(UnitSwitch, self).__init__(app, name)

        self.add_state("m", "Messages")
        self.add_state("b", "Bytes")

        self.brief_sing = {"m": "Msg.", "b": "Byte"}
        self.brief_plur = {"m": "Msgs.", "b": "Bytes"}

    def get_brief_singular(self, session):
        return self.brief_sing[self.get(session)]

    def get_brief_plural(self, session):
        return self.brief_plur[self.get(session)]

class PhaseSwitch(StateSwitch):
    def __init__(self, app, name):
        super(PhaseSwitch, self).__init__(app, name)

        self.add_state("a", "Active")
        self.add_state("i", "Idle")
        self.add_state("d", "Deleted")

    def get_sql_constraint(self, session, *args):
        phase = self.get(session)

        if phase == "a":
            sql = "((c.qmf_update_time is null or " + \
                "c.qmf_update_time > now() - interval '10 minutes')" + \
                " and qmf_delete_time is null)"
        elif phase == "i":
            sql = "((c.qmf_update_time is null or " + \
                "c.qmf_update_time <= now() - interval '10 minutes')" + \
                " and qmf_delete_time is null)"
        else:
            sql = "qmf_delete_time is not null"

        return sql

class SubmitSwitch(StateSwitch):
    """ Clicking on the link will submit the form.

        This uses javascript and a hidden input to
        submit the form when the link is clicked. This
        allows other fields on the form to "remember"
        their values. """
    def render_value(self, session, *args):
        return str(self.get(session))

    def render_name(self, session, *args):
        """ this needs to be the path of the param """
        return self.get_param_id()

    def render_item_link(self, session, state):
        title = self.get_title(state)
        hover = self.get_hover(state)
        class_ = self.get(session) == state and "selected"
        bm = self.get_bookmark(state)
        name = self.get_param_id()
        click = "submit_state('%s', '%s'); return false;" % (name, state)

        return fmt_link("", title, class_, link_title=hover, bm=bm, click=click)

class CuminItemTable(ItemTable):
    def __init__(self, app, name):
        super(CuminItemTable, self).__init__(app, name)

        self.paginator = Paginator(app, "page")
        self.add_child(self.paginator)

        self.update_enabled = True

    def do_process(self, session, *args):
        super(CuminItemTable, self).do_process(session, *args)

        self.paginator.set_count(session, self.get_item_count(session, *args))

class CuminTable(SqlTable):
    def __init__(self, app, name):
        super(CuminTable, self).__init__(app, name)

        self.html_class = CuminTable.__name__

        self.update_enabled = True

        self.paginator = Paginator(app, "page")
        self.add_child(self.paginator)

        self.links = self.Links(app, "links")
        self.links.html_class = "actions" # XXX fix this
        self.add_child(self.links)

    class Links(WidgetSet):
        def do_render(self, session):
            if len(self.children):
                return super(CuminTable.Links, self).do_render(session)

    def get_connection(self, session):
        return self.app.database.get_read_connection()

    def do_process(self, session, *args):
        super(CuminTable, self).do_process(session, *args)

        self.paginator.set_count(session, self.get_item_count(session, *args))

    def render_sql_limit(self, session, *args):
        start, end = self.paginator.get_bounds(session)
        return "limit %i offset %i" % (end - start, start)

class CuminTableWithControls(CuminTable):
    def __init__(self, app, name):
        super(CuminTableWithControls, self).__init__(app, name)

        self.switches = WidgetSet(app, "switches")
        self.switches.html_class = "switches"
        self.add_child(self.switches)

        self.filters = WidgetSet(app, "filters")
        self.filters.html_class = "filters"
        self.add_child(self.filters)

    def get_sql_constraint(self, session, *args):
        pass

    def render_switches(self, session, *args):
        if self.switches.children:
            return self.switches.render(session, *args)

    def render_filters(self, session, *args):
        if self.filters.children:
            return self.filters.render(session, *args)

    def get_sql_where_constraints(self, session, *args):
        constraints = super(CuminTableWithControls, self) \
            .get_sql_where_constraints(session, *args)

        for filter in self.filters.children:
            if filter:
                constraints.append(filter.get_sql_constraint(session, *args))

        constraint = self.get_sql_constraint(session, *args)

        if constraint:
            constraints.append(constraint)

        return constraints

class CuminSelectionTable(CuminTableWithControls, Form):
    def __init__(self, app, name, item_param):
        super(CuminSelectionTable, self).__init__(app, name)

        self.selection = ListParameter(app, "item", item_param)
        self.add_parameter(self.selection)

        self.checkboxes = CheckboxColumn(app, "id", self.selection)
        self.add_column(self.checkboxes)

        self.buttons = WidgetSet(app, "buttons")
        self.buttons.html_class = "buttons"
        self.add_child(self.buttons)

class CuminQMFSelectionTable(CuminSelectionTable):
    def filter_item(self, session, item):
        return True

    def get_item_count(self, session, *args):
        items = self.items.get(session)
        if not items:
            items = self.do_get_items(session, *args)

            self.items.set(session, items)

        count = 0
        for item in items:
            if self.filter_item(session, items[item]):
                count += 1
        return count

    def do_get_items(self, session, *args):
        raise Exception("not implemented")

    def render_items(self, session, *args):
        items = self.get_items(session, *args)
        rows = list()
        for item in items:
            data = dict()
            # filter them
            if self.filter_item(session, items[item]):
                data['id'] = item
                data['name'] = item
                for datum in items[item]:
                    data[datum] = items[item][datum]['VALUE']
                rows.append(data)

        # sort them
        scol = self.get_selected_column(session)
        rows = sorted(rows, key=lambda x: x[scol.name], reverse=self.reversed.get(session))

        # limit them
        page = self.paginator.page_index.get(session)
        items_per_page = self.paginator.page_size

        start = page * items_per_page
        stop = start + items_per_page
        rows = rows[start:stop]

        # render them
        writer = Writer()
        for row in rows:
            self.item_tmpl.render(writer, session, row)
        return writer.to_string()

class NullSortColumn(SqlTableColumn):
    def get_order_by_sql(self, session):
        key = self.get_column_key(session)

        if key:
            dir = self.parent.is_reversed(session) and "desc" or "asc"
            return "order by %s_is_null asc, %s %s" % (key, key, dir)

class FreshDataOnlyColumn(SqlTableColumn):
    def __init__(self, app, name):
        super(FreshDataOnlyColumn, self).__init__(app, name)

        self.__ago = self.TimeAgo(app, "ago")
        self.add_attribute(self.__ago)

    def render_content(self, session, data):
        key = self.get_column_key(session)
        value = data["qmf_update_time"]

        if value and value > self.__ago.get(session):
            html = self.render_value(session, data[key])
        else:
            html = fmt_none_brief()

        return html

    class TimeAgo(Attribute):
        def get_default(self, session):
            return datetime.now() - timedelta(minutes=10)

class StaticTableColumnHeader(ItemTableColumnHeader):
    pass

class StaticColumnHeader(TableColumnHeader):
    pass

class NonSortableTableColumn(ItemTableColumn):
    def __init__(self, app, name):
        super(NonSortableTableColumn, self).__init__(app, name)

        self.header_class = StaticTableColumnHeader

class PaginatedItemSet(ItemSet):
    def __init__(self, app, name):
        super(PaginatedItemSet, self).__init__(app, name)

        self.paginator = Paginator(app, "page")
        self.add_child(self.paginator)

    def do_process(self, session, *args):
        super(PaginatedItemSet, self).do_process(session, *args)

        self.paginator.set_count(session, self.get_item_count(session, *args))

    def get_bounds(self, session):
        return self.paginator.get_bounds(session)

class CheckboxInputColumn(FormInput, ItemTableColumn):
    def __init__(self, app, name, item_param):
        super(CheckboxInputColumn, self).__init__(app, name, None)

        self.header_class = CheckboxIdColumnHeader
        self.width = "2em"

        self.param = ListParameter(app, "param", item_param)
        self.add_parameter(self.param)

    def do_render(self, session, data):
        name = self.param.path
        id = data[self.name]
        attr = id in self.param.get(session) and "checked=\"checked\"" or ""
        click = self.parent.update_enabled and " onclick=\"cumin.clickTableCheckbox(this, '%s')\"" % name or ""
        html = "<td><input type=\"checkbox\" name=\"%s\" " + \
            "value=\"%i\" %s%s/></td>"

        return html % (name, id, attr, click)

class CheckboxColumn(FormInput, SqlTableColumn):
    def __init__(self, app, name, param):
        super(CheckboxColumn, self).__init__(app, name, param)

        self.header_class = CheckboxColumnHeader
        self.width = "2em"

    def do_render(self, session, data, disabled=False):
        name = self.param.path
        id = data[self.get_column_key(session)]
        attr = id in self.param.get(session) and "checked=\"checked\"" or ""
        disa = disabled and "disabled=\"disabled\"" or ""
        click = self.parent.update_enabled and \
            "onclick=\"cumin.clickTableCheckbox(this, '%s')\"" % name or ""

        html = """<td><input type="checkbox" name="%s" value="%s" %s/></td>"""
        attrs = " ".join((attr, disa, click))

        return html % (name, str(id), attrs)

class CheckboxIdColumn(FormInput, SqlTableColumn):
    def __init__(self, app, name):
        super(CheckboxIdColumn, self).__init__(app, name, None)

        self.header_class = CheckboxIdColumnHeader

        item = IntegerParameter(app, "param")
        self.add_parameter(item) # XXX lose this?

        self.param = ListParameter(app, "id", item)
        self.add_parameter(self.param)

    def clear(self, session):
        self.param.set(session, list())

    def do_render(self, session, data, disabled=False):
        name = self.param.path
        id = data[self.name]
        attr = id in self.param.get(session) and "checked=\"checked\"" or ""
        disa = disabled and "disabled=\"disabled\"" or ""
        click = self.parent.update_enabled and " onclick=\"cumin.clickTableCheckbox(this, '%s')\"" % name or ""
        t = "<td><input type=\"checkbox\" name=\"%s\" value=\"%s\" %s %s%s/></td>"

        return t % (name, str(id), attr, disa, click)

class CheckboxStringIdColumn(CheckboxIdColumn):
    def __init__(self, app, name):
        """ calls wrong super to avoid adding integer param """
        super(CheckboxIdColumn, self).__init__(app, name, None)

        self.header_class = CheckboxIdColumnHeader

        item = Parameter(app, "param")
        self.add_parameter(item)

        self.param = ListParameter(app, "id", item)
        self.add_parameter(self.param)

class CheckboxColumnHeader(ItemTableColumnHeader):
    def render_form_id(self, session, *args):
        return self.column.form.path

    def render_elem_name(self, session, *args):
        return self.column.param.path

 # XXX remove this
class CheckboxIdColumnHeader(CheckboxColumnHeader):
    pass

class FilteredCheckboxIdColumn(CheckboxIdColumn):
    def __init__(self, app, name, form, callback=None):
        super(FilteredCheckboxIdColumn, self).__init__(app, name)

        # call back that returns True if the checkbox is to be disabled
        self.__callback = callback

    def do_render(self, session, data):
        disabled = self.__callback and self.__callback(session, data) or False
        return super(FilteredCheckboxIdColumn, self).do_render(session, data,
            disabled=disabled)

class FilteredCheckboxColumn(CheckboxColumn):
    def __init__(self, app, name, param, callback):
        super(FilteredCheckboxColumn, self).__init__(app, name, param)

        # call back that returns True if the checkbox is to be disabled
        self.__callback = callback

    def do_render(self, session, data):
        disabled = self.__callback and self.__callback(session, data) or False
        return super(FilteredCheckboxColumn, self).do_render \
            (session, data, disabled=disabled)

class NameField(StringField):
    def __init__(self, app, name):
        super(NameField, self).__init__(app, name)

        self.required = True
        self.illegal_chars = ""
        self.legal_chars_desc = None

    def render_title(self, session):
        return "Name"

    def validate(self, session):
        name = self.get(session)

        if name == "" and self.required:
            self.form.errors.add(session, MissingValueError(self))
        else:
            for char in self.illegal_chars:
                if char in name:
                    msg = "The name contains illegal characters"

                    if self.legal_chars_desc:
                        msg = msg + "; " + self.legal_chars_desc

                    self.form.errors.add(session, FormError(msg))

                    break

# XXX what?
class TextField(NameField):
    def __init__(self, app, name):
        super(TextField, self).__init__(app, name)

        self.__title = "Title"

    def set_title(self, title):
        self.__title = title

    def render_title(self, session):
        return self.__title

class ExchangeNameField(NameField):
    def __init__(self, app, name):
        super(ExchangeNameField, self).__init__(app, name)

        self.illegal_chars = " (){}[]-<>&%"
        self.legal_chars_desc = """
            The exchange name is invalid; allowed characters are
            letters, digits, ".", and "_"
            """

class UniqueNameField(NameField):
    def __init__(self, app, name, cls, fld="name"):
        super(UniqueNameField, self).__init__(app, name)

        self.__class = cls
        self.__field = fld
        self.__object = None

    def set_object_attr(self, attr):
        self.__object = attr

    def validate(self, session):
        super(UniqueNameField, self).validate(session)

        name = self.get(session)

        if name:
            args = {self.__field: name, }
            results = self.__class.selectBy(**args)

            if self.__object:
                object = self.__object.get(session)

                if object:
                    results = results.filter(self.__class.q.id != object.id)

                if results.count() > 0:
                    self.form.errors.add(session, DuplicateValueError())

class DuplicateValueError(FormError):
    def __init__(self, fld="name"):
        super(DuplicateValueError, self).__init__()

        self.__field = fld

    def get_message(self, session):
        return "An item with this %s already exists" % self.__field

class TwoOptionRadioField(RadioField):
    def __init__(self, app, name, option1="yes", option2="no"):
        super(TwoOptionRadioField, self).__init__(app, name, None)

        self.param = Parameter(app, "param")
        self.param.default = option2
        self.add_parameter(self.param)

        option = self.Option1(app, option1, self.param)
        self.add_option(option)

        option = self.Option2(app, option2, self.param)
        self.add_option(option)

    def render_title(self, session):
        return "Pick an option"

    def render_title_1(self, session):
        pass

    def render_title_2(self, session):
        pass

    class Option1(RadioFieldOption):
        def render_title(self, session):
            return self.parent.render_title_1(session)

    class Option2(RadioFieldOption):
        def render_title(self, session):
            return self.parent.render_title_2(session)

class MultiplicityField(RadioField):
    def __init__(self, app, name):
        super(MultiplicityField, self).__init__(app, name, None)

        self.param = Parameter(app, "param")
        self.param.default = "all"
        self.add_parameter(self.param)

        self.add_option(self.All(app, "all", self.param))
        self.add_option(self.Top(app, "top", self.param))
        self.top_n = self.TopN(app, "topn", self.param)
        self.add_option(self.top_n)

    def render_title(self, session):
        return "Select all, the top message or the top n messages"

    class All(RadioFieldOption):
        def render_value(self, session):
            return "all"

        def render_title(self, session):
            return "All"

    class Top(RadioFieldOption):
        def render_value(self, session):
            return "top"

        def render_title(self, session):
            return "Top message"

    class TopN(RadioFieldOption):
        def __init__(self, app, name, param):
            super(MultiplicityField.TopN, self).__init__(app, name, param)

            self.__n_value = IntegerParameter(app, "arg")
            self.add_parameter(self.__n_value)

        def render_value(self, session):
            return "N"

        def render_arg_name(self, session):
            return self.__n_value.path

        def render_arg_value(self, session):
            return 0

        def get_n_value(self, session):
            return self.__n_value.get(session)

        def render_title(self, session):
            return

class AjaxField(Widget):
    """ Update a single span or div after the page loads """

    def render_script(self, session):
        script = """
        <script type="text/javascript">
        window.addEvent('domready', function get_%s() {
            var now = new Date();
            wooly.backgroundUpdate('%s'+';ts='+now.getTime(), got_%s, "%s");
        });
        </script>
        """
        get_fn = self.get_fn(session)
        url = self.get_url(session)
        got_fn = self.got_fn(session)
        elem_id = self.elem_id(session)

        return url and script % (get_fn, url, got_fn, elem_id) or ""

    def get_url(self, session):
        pass

    def get_fn(self, session):
        return self.name

    def got_fn(self, session):
        return self.name

    def elem_id(self, session):
        return self.name

class MoreFieldSet(FormFieldSet, FormField):
    """ Displays a button that opens and closes a set of fields

        Used in a FieldForm as a FormField. Instead of calling
        add_field on the FieldForm, call add_field on this.
        For example:
            self.more = MoreFieldSet(app, "more")
            self.add_field(self.more)

            self.name = NameField(app, "name")
            self.more.add_field(self.name)

            self.port = StringField(app, "port")
            self.more.add_field(self.port)
        """
    def __init__(self, app, name):
        super(MoreFieldSet, self).__init__(app, name)

        self.input = HiddenInput(app, "open")
        self.add_child(self.input)

    def render_inputs(self, session, *args):
        return self.render_fields(session, *args)

    def render_more_text(self, session, *args):
        return "Show Advanced Options..."

    def render_less_text(self, session, *args):
        return "Hide Advanced Options..."

    def render_state_text(self, session, *args):
        return self.input.get(session) \
            and self.render_less_text(session, *args) \
            or self.render_more_text(session, *args)

    def render_open_state(self, session, *args):
        return self.input.do_marshal(self.input.get(session))

    def render_open_path(self, session, *args):
        return self.input.render_name(session, *args)

    def render_open_display(self, session, *args):
        return self.input.get(session) and "block" or "none"

class Wait(Widget):
    pass

# XXX this should move somewhere else
class LoginSession(object):
    def __init__(self, app, user, group):
        self.app = app

        # If this is an external user, create
        # an adapter here.  Lots of things
        # expect user.name to be defined.
        if type(user) is str:
            self.user = LoginSession.ExternalUser()
            self.user.name = user
        else:
            self.user = user

        self.group = group
        self.created = datetime.now()
        self.notifications = list()

    class ExternalUser(object):
        pass

class NotificationSet(Widget):
    def __init__(self, app, name):
        super(NotificationSet, self).__init__(app, name)

        self.update_enabled = True

        self.dismiss = IntegerParameter(app, "dismiss")
        self.add_parameter(self.dismiss)
        
        self.dismiss_all = BooleanParameter(app, "dismiss_all")
        self.add_parameter(self.dismiss_all)

        self.item_widget = NotificationItem(app, "item")
        self.add_child(self.item_widget)

    def get_items(self, session):
        items = session.get_notifications()
        if self.app.notification_timeout > 0:
            for i in items:
                # we want the messages to timeout after 3 min, the easiest way
                # is to dismiss it doing it here for now so that both 
                # TaskInvocations and Notifications will be handled in the 
                # same place. The value for the timeout can be changed via the 
                # notification-timeout config
                if not i.dismissed and datetime.now() - i.timestamp >= \
                   timedelta(seconds=self.app.notification_timeout):
                    i.dismissed = True
        items = [x for x in items if not x.dismissed]
        return items

    def do_process(self, session):
        super(NotificationSet, self).do_process(session)

        dismiss = self.dismiss.get(session)
        dismiss_all = self.dismiss_all.get(session)
        
        if dismiss_all:
            for invoc in self.get_items(session):
                invoc.dismissed = True
# We're leaking task invocations during the login session.
# Replace the loop with the following at a later date
#            items[:] = []
            self.dismiss_all.set(session, self.dismiss_all.default)
                    
        if dismiss:
            for invoc in self.get_items(session):
                if id(invoc) == dismiss:
                    invoc.dismissed = True
                    break
# We're leaking task invocations during the login session.
# Replace the loop with the following at a later date
#            items[:] = [x for x in items if id(x) != dismiss]
            self.dismiss.set(session, self.dismiss.default)


    def do_render(self, session):
        items = self.get_items(session)

        if items:
            return super(NotificationSet, self).do_render(session)

    def render_items(self, session):
        writer = Writer()

        for item in self.get_items(session):
            writer.write(self.item_widget.render(session, item))

        return writer.to_string()
    
    def render_dismiss_all_href(self, session):
        branch = session.branch()
        self.dismiss_all.set(branch, True)
        return branch.marshal()

class NotificationItem(Widget):
    def render_icon_href(self, session, item):
        return "resource?name=add-20.png"

    def render_message(self, session, item):
        return item.get_message(session)

    def render_dismiss_href(self, session, item):
        branch = session.branch()
        self.parent.dismiss.set(branch, id(item))
        return branch.marshal()

class CuminPage(HtmlPage):
    def __init__(self, app, name):
        super(CuminPage, self).__init__(app, name)

        self.protected = True

        self.user = UserAttribute(app, "user")
        self.add_attribute(self.user)

        self.error_tmpl = WidgetTemplate(self, "error_html")
        self.not_found_tmpl = WidgetTemplate(self, "not_found_html")

    def _redirect_to_login(self, session):
        session.cursor = self.app.database.get_read_cursor()
        if not self.authorized(session):
            page = self.app.login_page
            sess = Session(page)
            page.origin.set(sess, session.marshal())
            self.redirect.set(session, sess.marshal())
            return True
        return False

    def redirect_on_not_authorized(self, session):
        # If the user is not logged in, then it doesn't have a
        # a group identity yet.  Check to see if we should
        # redirect to the login page before looking for a
        # valid page to redirect to based on group
        if not self._redirect_to_login(session):
            super(CuminPage, self).redirect_on_not_authorized(session)

    def do_process(self, session):
        if not self._redirect_to_login(session):
            super(CuminPage, self).do_process(session)

    def authorized(self, session):
        if not self.protected:
            return True

        login = session.client_session.attributes.get("login_session")
        if login:
            when = datetime.now() - timedelta(hours=24)
            if login.created > when:
                return True

        elif self.app.auth_proxy or self.app.user:
            username = self.app.user
            # proxy user overrides app defined user 
            if self.app.auth_proxy:
                try:
                    username = session.request_environment['HTTP_REMOTE_USER']
                except KeyError:
                    log.debug("Proxy auth enabled but no remote user set")

            if username:
                user, ok = self.app.authenticator.find_user(username)
                if not ok:
                    # We couldn't find the user, internally or externally
                    if not self.app.auth_proxy:
                        log.info("User '%s' not found" % username)
                        return False
                    else:
                        log.info("User %s not found in db, "\
                                     "using auth proxy", username )
                        #Hmmm, what is users here?  For now just let it return
                        # to the login page
                        return False

#TODO prehodit do authenticatora
# ondemand -> authenticator.create_user
# user -> authenticator.force_login

                # Check for valid group
                if self.app.authorizator.is_enforcing():
                    if not user:
                        # This is an external user, default role is 'user'
                        roles = ['user']
                    else:
                        cursor = self.app.database.get_read_cursor()
                        roles = self.app.admin.get_roles_for_user(
                                                            cursor, user)
                    if not self.app.authorizator.contains_valid_group(roles):
                        log.info("No valid roles for '%s'" % username)
                        return False # go to login page
                else:
                    roles = []

                if user is None:
                    user = username
                login = LoginSession(self.app, user, roles)

                # We want to generate a new session id and record the
                # login while keeping the rest of the session data.  
                # This is to protect against session fixation attacks.
                self.app.server.reset_client_session_id(session, login)
                return True
        return False

    def redirect_on_exception(self, session):
        # If we have certain exceptions, redirect to the main page with a
        # notice instead of using the standard templates. Test for presence
        # on the main page already to avoid any possibility of an infinite
        # redirect loop.
        cls, value, traceback = sys.exc_info()
        mainpage = self.lookup_mainpage(session)
        if session.request_environment["REQUEST_URI"] != mainpage:
            if cls is RosemaryNotFound:
                session.add_notice(Notice(
                        "An object being displayed became unavailable"))
            elif cls is CSRFException:
                session.add_notice(Notice("An invalid form was submitted"))
            else:
                mainpage = None

        return mainpage

    def render_error(self, session):
        cls, value, traceback = sys.exc_info()

        writer = Writer()

        if cls is RosemaryNotFound:
            self.not_found_tmpl.render(writer, session)
        else:
            self.error_tmpl.render(writer, session)

        return writer.to_string()

    def render_error_dump(self, session):
        return self.error.get(session).render()

class CuminFormPage(CuminPage):
    def __init__(self, app, name):
        super(CuminFormPage, self).__init__(app, name)

        self.background = self.Background(app, "background")
        self.background.type = "text/html"
        self.add_child(self.background)

        self.modes = ModeSet(app, "modes")
        self.add_child(self.modes)

        # XXX look into this
        # for form in model tasks:
        #    self.add_mode(form)

    def render_content(self, session):
        writer = Writer()

        writer.write(self.modes.render(session))
        writer.write(self.background.render(session))

        return writer.to_string()

    class Background(BackgroundInclude):
        def render_data(self, session):
            form = self.parent.modes.mode.get(session)
            url = form.return_url.get(session)
            return url

class CuminExportPage(CsvPage):
    def __init__(self, app, name):
        super(CuminExportPage, self).__init__(app, name)

        self.modes = ModeSet(app, "modes")
        self.add_child(self.modes)

        self.filtered = Parameter(app, "filtered")
        self.add_parameter(self.filtered)

        self.file_name = Parameter(app, "file")
        self.add_parameter(self.file_name)

        cls = Parameter(app, "class")
        self.classes = ListParameter(app, "classes", cls)
        self.add_parameter(self.classes)

        package = Parameter(app, "package")
        self.packages = ListParameter(app, "packages", package)
        self.add_parameter(self.packages)

        agent = Parameter(app, "qmf_obj_id")
        self.agents = ListParameter(app, "agents", agent)
        self.add_parameter(self.agents)

    def render_content(self, session, *args):
        writer = Writer()

        mode = self.modes.mode.get(session)
        objects = self.get_objects(session)
        for obj, mobj in zip(objects, mode.objects):
            mobj.set(session, obj)

        writer.write(mode.render(session))

        return writer.to_string()

    def do_process(self, session):
        session.cursor = self.app.database.get_read_cursor()

    def get_objects(self, session):
        classes = self.classes.get(session)
        packages = self.packages.get(session)
        agents = self.agents.get(session)

        objects = list()
        cursor = self.app.database.get_read_cursor()

        for cls, package, agent in zip(classes, packages, agents):
            rosemary_package = self.app.model._packages_by_name[package]
            rosemary_cls = rosemary_package._classes_by_name[cls]
            objects.append(rosemary_cls.get_object(cursor, _qmf_object_id=agent))

        return objects

    def get_file_name(self, session):
        name = self.file_name.get(session)
        return "%s.csv" % name

    def set_parameters(self, nsession, session, attribs, name):
        self.file_name.set(nsession, name)
        for attrib in attribs:
            if attrib is not None:
                obj = attrib.get(session)
                cls = obj._class
                self.packages.add(nsession, cls._package._name)
                self.classes.add(nsession, cls._name)
                self.agents.add(nsession, obj._qmf_object_id)

class IncrementalSearchInput(StringInput, ItemSet):
    def __init__(self, app, name, field_param):
        super(IncrementalSearchInput, self).__init__(app, name)

        self.disabled_tmpl = WidgetTemplate(self, "disabled_html")
        self.field = field_param

    def do_get_items(self, session):
        return ()

    def render_name(self, session):
        return self.field.path

    def do_render(self, session, *args):
        if self.disabled:
            writer = Writer()

            self.disabled_tmpl.render(writer, session, *args)

            return writer.to_string()
        else:
            return super(IncrementalSearchInput, self).do_render(session, *args)

class BaseBindingInput(IncrementalSearchInput):
    def __init__(self, app, name, field_param):
        super(BaseBindingInput, self).__init__(app, name, field_param)

    def render_item_content(self, session, field):
        return xml_escape(field.name) or "Default"

    def render_value(self, session):
        if self.disabled:
            field = self.form.object.get(session)
            return fmt_shorten(field.get_formatted_value("name", escape=True),
                                          pre=36, post=4, spanify=False)
        else:
            input_value = self.param.get(session)
            return input_value and xml_escape(input_value) or ""

    def base_get_items(self, session, objects):
        obj_list = []
        if not self.disabled:
            obj_list_full = sorted_by(list(objects))

            delta = timedelta(days=3)
            for _obj in obj_list_full:
                if (_obj._qmf_update_time > (datetime.now() - delta)):
                    obj_list.append(_obj)

        return obj_list

class BindingAddTask(ObjectFrameTask):
    def get_title(self, session):
        return "Add binding"

    def do_invoke(self, invoc, obj, queue, exchange, key, args):
        session = self.app.model.get_session_by_object(obj)
        session.exchange_bind(queue=queue, exchange=exchange,
                              binding_key=key, arguments=args)
        session.sync()

        invoc.end()

class QueueBindingField(ScalarField):
    def __init__(self, app, name, queue):
        super(QueueBindingField, self).__init__(app, name, None)

        self.input = QueueInput(app, "input", queue)
        self.add_child(self.input)

    def render_title(self, session):
        return "Queue"

class ExchangeBindingField(ScalarField):
    def __init__(self, app, name, exchange):
        super(ExchangeBindingField, self).__init__(app, name, None)

        self.input = ExchangeInput(app, "input", exchange)
        self.add_child(self.input)

    def render_title(self, session):
        return "Exchange"

class QueueInput(BaseBindingInput):
    def do_get_items(self, session):
        cls = self.app.model.org_apache_qpid_broker.Queue
        queue = self.form.object.get(session)
        vhostid = queue._vhostRef_id
        queues = cls.get_selection(session.cursor, _vhostRef_id=vhostid)
        return self.base_get_items(session, queues)

class ExchangeInput(BaseBindingInput):
    def do_get_items(self, session):
        cls = self.app.model.org_apache_qpid_broker.Exchange
        obj = self.form.object.get(session)
        vhostid = obj._class._name == "Vhost" and obj._id or obj._vhostRef_id
        exchanges = cls.get_selection(session.cursor, _vhostRef_id=vhostid)
        return self.base_get_items(session, exchanges)

class TopTable(ObjectTable):
    def __init__(self, app, name, cls):
        super(TopTable, self).__init__(app, name, cls)

        col = ObjectTableColumn(app, cls._id.name, cls._id)
        col.visible = False
        self.add_column(col)

        self.header = TopTableHeader(app, "header")
        self.replace_child(self.header)

        self.footer = TopTableFooter(app, "footer")
        self.replace_child(self.footer)

        self.header.limit.default = 5

    def get_count(self, session):
        # avoid extra sql call since we don't show the record count
        return 0

class TopTableHeader(TableHeader):
    def __init__(self, app, name):
        super(TopTableHeader, self).__init__(app, name)

        self.font = Attribute(app, "font")
        self.font.default = 0.9
        self.add_attribute(self.font)

        self.limit = Attribute(app, "limit")
        self.limit.default = 5
        self.add_attribute(self.limit)

        self.offset = Attribute(app, "offset")
        self.offset.default = 0
        self.add_attribute(self.offset)

    def init(self):
        super(TopTableHeader, self).init()

        for column in self.table.columns:
            column.header = TopTableColumnHeader(self.app, "header")
            column.replace_child(column.header)
            column.header.init()

class TopTableColumnHeader(TableColumnHeader):
    def render_class(self, session):
        return self.parent.name

class TopTableColumn(ObjectTableColumn):
    def render_class(self, session):
        return self.name

class TopTableFooter(Widget):
    def render(self, session):
        return ""
    
class AboutPage(CuminPage, ModeSet):
    def __init__(self, app, name):
        super(AboutPage, self).__init__(app, name)

        self.about = AboutMainView(app, "about")
        self.add_mode(self.about)
        self.set_default_frame(self.about)

    def render_title(self, session):
        return "About"
    
class AboutFrame(Frame):
    def __init__(self, app, name):
        super(AboutFrame, self).__init__(app, name)
        content = AboutContent(app, "about_content")
        self.add_child(content)
        browsers = AboutSupportedBrowsers(app, "browsers")
        self.add_child(browsers)

    def render_title(self, session):
        return "About the console"    
    
class AboutMainView(CuminMainView):
    def __init__(self, app, name):
        super(AboutMainView, self).__init__(app, name)

        self.about = AboutFrame(app, "about")
        self.add_tab(self.about)

class AboutSupportedBrowsers(Widget):
    def __init__(self, app, name):
        super(AboutSupportedBrowsers, self).__init__(app, name)
        
        self.browsers = ["Firefox 10", \
                         "Internet Explorer 8", \
                         "Safari 5"]
        
    def render_browser_list(self, session):
        browser_list_items = ""
        for browser in self.browsers:
            browser_list_items += "<li class='browseritem'>%s</li>" % browser
            
        return browser_list_items
        
class AboutContent(Widget):
    def __init__(self, app, name):
        super(AboutContent, self).__init__(app, name)

        self.version_string = ""
        self.version_local = False

    # Look for version info in our well-known file.
        version_path = os.path.join(self.app.home, "version")
        if os.path.isfile(version_path):
            # Permission errors or corrupt file always possible
            try:
                f = open(version_path)
                self.version_string = f.readline().strip()
                self.version_local = f.readline().strip() == "local"
            except:
                pass

        if len(self.version_string) == 0:
            self.version_string = "Version has not been set"

    def render_version(self, session):
        res = self.version_string
        if self.version_local:
            res += ", devel instance"
        return res       
    
class PageableFilteredSelect(CheckboxItemSetField):
    def __init__(self, app, name):
        item_parameter = SymbolParameter(app, "iparam")    
        super(PageableFilteredSelect, self).__init__(app, name, item_parameter)    
        self.container_height = 375
        self.container_width = 250
        self.width = 400
        self.items_per_page = 15
        self.listcontainer_height = 270

    def render_items(self, session):
        items = self.do_get_items(session)
        items_string = ""
   
        for i, item in enumerate(items):
            items_string = items_string + "<option id='" + str(i) + "' name='" + item + "' value='" + item + "'" + ">" + item + "</option>"
            
        return items_string        
        
    def render_datasrc(self, session):
        return "multiselect"
    
    def render_class(self, session):
        return "mtmultiselect"
    
    def render_selected_class(self, session):
        return "selected"
    
    def render_items_per_page(self, session):
        return self.items_per_page
    
    def render_title(self, session):
        return "Make your selections"
    
    def render_width(self, session):
        return "%dpx" % self.width
    
    def render_container_width(self, session):
        return "%dpx" % self.container_width
    
    def render_container_height(self, session):
        return "%dpx" % self.container_height
    
    def render_listcontainer_height(self, session):
        return "%dpx" % self.listcontainer_height

    
