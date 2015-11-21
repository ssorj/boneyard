from cumin.objectframe import ObjectFrame
from cumin.qmfadapter import ObjectQmfAdapter, ObjectQmfField
from cumin.sqladapter import ObjectSqlAdapter, ObjectSqlField
from cumin.util import Identifiable, xml_escape

from rosemary.model import RosemaryClass, RosemaryAttribute, RosemaryReference
from rosemary.sqlfilter import SqlFilter, SqlLikeFilter, SqlValueFilter, SqlDateValueFilter

from wooly.util import StringCatalog, Writer, escape_entity
from wooly.datatable import DataTable, DataTableColumn
from wooly import Attribute, Widget, SessionAttribute, Parameter
from wooly.forms import Form, StringInput, FoldingFieldSubmitForm, OptionInputSet
from cumin.objecttask import ObjectTaskButton, ObjectTask
from wooly.parameters import IntegerParameter, ListParameter, StringParameter
from wooly.table import CheckboxColumnCell, CheckboxColumnHeader,\
    CheckboxColumnInput, LinkColumn
from wooly.widgets import WidgetSet, ItemSet
import wooly
from wooly.template import WidgetTemplate
from cumin.formats import fmt_bytes


strings = StringCatalog(__file__)

class ObjectTable(DataTable):
    def __init__(self, app, name, cls):
        super(ObjectTable, self).__init__(app, name)

        assert isinstance(cls, RosemaryClass), cls

        self.cls = cls

        self.update_enabled = True

        # (RosemaryAttribute this, RosemaryAttribute that, Attribute object)
        self.filter_specs = list()

        # ((RosemaryAttribute this, Attribute value, SqlLikeFilter.CONTAINS)
        self.like_specs = list()

        self.export = None

    def init(self):
        if not self.adapter:
            self.adapter = ObjectSqlAdapter(self.app, self.cls)

        super(ObjectTable, self).init()

        for this, that, fobj in self.filter_specs:
            self.adapter.add_value_filter(this)

        for column, vattr, type in self.like_specs:
            self.adapter.add_like_filter(column.attr)

        if self.sort.default is None:
            for col in self.columns:
                if col.sortable:
                    self.set_default_sort_column(col)
                    break

        # Now that all columns have been initialized, and we
        # have a sortable column if possible, set direction
        self.set_default_sort_direction()

    def add_attribute_column(self, attr):
        assert isinstance(attr, RosemaryAttribute), attr

        col = ObjectTableColumn(self.app, attr.name, attr)

        self.add_column(col)

        return col

    def add_filter(self, attribute, this, that=None):
        if not that:
            that = this

        assert isinstance(attribute, Attribute), attribute
        assert isinstance(this, RosemaryAttribute), this
        assert isinstance(that, RosemaryAttribute), that

        self.filter_specs.append((this, that, attribute))

    def add_reference_filter(self, attribute, ref):
        assert isinstance(ref, RosemaryReference), ref

        this = ref
        that = ref.that_cls._id

        self.add_filter(attribute, this, that)

    def add_like_filter(self, attribute, column, type=SqlLikeFilter.CONTAINS):
        assert isinstance(attribute, Attribute), attribute
#        assert isinstance(column, DataTableColumn), column

        self.like_specs.append((column, attribute, type))

    def get_data_values(self, session):
        values = dict()

        for this, that, fobj in self.filter_specs:
            obj = fobj.get(session)
            values[this.name] = getattr(obj, that.name)

        for this, vattr, type in self.like_specs:
            value = vattr.get(session)
            # if the user typed a %, don't add another
            pre = ""
            post = "%"
            if not "%" in value:
                pre = type == SqlLikeFilter.CONTAINS and "%%" or ""
            else:
                post = ""
            values[this.attr.name] = "%s%s%s" % (pre, value, post)

        return values

    def render_title(self, session):
        return "%ss" % self.cls._title

    def render_footer_options(self, session):
        if self.export:
            return self.export.render(session)

class CsvExporter(Widget):
    def __init__(self, app, name, args, data_source):
        super(CsvExporter, self).__init__(app, name)

        # 0 or more RosemaryAttributes that need to be set
        # for the selector's table to get it's data
        self.objects = list(args)

        self.data_source = data_source

        # avoid name collisions on csv page
        while self.name in self.app.export_page.modes.children_by_name:
            self.name = self.name + ".1"

        self.app.export_page.modes.add_mode(self)

    def render(self, session):
        writer = Writer()

        # put out the column headers
        writer.write(",".join(self.render_csv_header(session)))
        writer.write("\n")

        # put out the data
        data = self.get_data(session)
        for record in data:
            writer.write(",".join(self.render_csv_cells(session, record)))
            writer.write("\n")

        return writer.to_string()

    def render_csv_header(self, session):
        return []

    def render_csv_cells(self, session, record):
        return []

    def _safe_value(self, value):
        # Cconvert None to ""
        # Ensure there are no commas. There is no standard way to handle this so
        # we are just replacing each comma with a space
        return value is not None and str(value).replace(",", " ") or ""

class CsvStatsExporter(CsvExporter):
    # stats only have 1 row of data
    # each col in that row is a stat
    def get_data(self, session):
        return (1,)

    # the col header is the stat title
    def render_csv_header(self, session):
        items = self.data_source.do_get_items(session)
        return  [self._safe_value(self.data_source.render_item_title(session, x)) for x in items]

    # the col value is the stat value
    def render_csv_cells(self, session, record):
        items = self.data_source.do_get_items(session)
        return  [self._safe_value(self.data_source.render_item_value(session, x)) for x in items]

class CsvTableExporter(CsvExporter):
    def get_data(self, session):
        table = self.data_source.table

        values = table.get_data_values(session)
        options = table.get_data_options(session)
        # get all the records, starting at the beginning
        options.limit = None
        options.offset = 0

        return table.adapter.get_data(values, options)

    def render_csv_header(self, session):
        cells = list()
        for column in self.data_source.table.get_visible_columns(session):
            if column.name != "id":
                value = column.render_header_content(session)
                value = self._safe_value(value)
                cells.append(value)

        return cells
        
    def render_csv_cells(self, session, record):
        cells = list()
        for column in self.data_source.table.get_visible_columns(session):
            # don't output the checkbox column since it's just a database id
            if column.name != "id":
                value = column.cell.render_content(session, record)
                value = self._safe_value(value)
                cells.append(value)

        return cells

class ObjectTableColumn(DataTableColumn):
    def __init__(self, app, name, attr):
        super(ObjectTableColumn, self).__init__(app, name)

        self.attr = attr

    def init(self):
        super(ObjectTableColumn, self).init()

        assert self.table.adapter, self.table

        try:
            self.field = self.table.adapter.fields_by_attr[self.attr]
        except KeyError:
            cls = getattr(self.table.adapter, "default_field_cls", ObjectSqlField)
            self.field = cls(self.table.adapter, self.attr)

            format = self.attr.unit
            if format:
                if format == "MiB":
                    self.field.format = self.fmt_mb
                elif format == "KiB":
                    self.field.format = self.fmt_kb

    def render_header_link_class(self, session):
        return "TableColumnHeader"

    def fmt_b(self, value):
        return value is not None and fmt_bytes(value) or None

    def fmt_kb(self, value):
        return value is not None and fmt_bytes(value * 1024) or None

    def fmt_mb(self, value):
        return value is not None and fmt_bytes(value * 1024 * 1024) or None

class ObjectSelector(Form):
    def __init__(self, app, name, cls, object=None):
        super(ObjectSelector, self).__init__(app, name)

        self.update_enabled = False
        self.cls = cls

        self.switches = ObjectSelectorSwitches(app, "switches")
        self.add_child(self.switches)

        self.selectablefilters = ObjectSelectorSelectableFilters(app, "selectablefilters")
        self.add_child(self.selectablefilters)

        self.filters = ObjectSelectorFilters(app, "filters")
        self.add_child(self.filters)

        self.buttons = ObjectSelectorButtons(app, "buttons")
        self.add_child(self.buttons)

        self.links = ObjectSelectorLinks(app, "links")
        self.add_child(self.links)

        self.table = self.create_table(app, "table", cls)
        self.add_child(self.table)

        self.tasks = list()

    def init(self):
        super(ObjectSelector, self).init()

        for task in self.tasks:
            task.init()

        for task in self.tasks:
            button = ObjectTaskButton(self.app, task)
            self.buttons.add_child(button)
            button.init()

    def create_table(self, app, name, cls):
        return ObjectSelectorTable(app, name, cls)

    def enable_csv_export(self, *args):
        assert self.table

        exporter = CsvTableExporter(self.app, self.name + "_csv", args, self)

        self.table.export = ExportButton(self.app, "export", args, exporter, self.cls._title)
        self.table.add_child(self.table.export)

    def add_search_filter(self, this):
        search = StringInput(self.app, "search")
        search.param.default = ""
        search.title = "Search in %s column" % this.attr.title

        self.table.add_like_filter(search.param, this)
        self.filters.add_child(search)
        
    def add_selectable_search_filter(self, inputSet):
        search = StringInput(self.app, "search")
        search.param.default = ""
        search.title = "Search in column"
        search.size = 35

        self.selectablefilters.add_child(search)        
        self.selectablefilters.add_child(inputSet)
        

    def render_search_id(self, session):
        if len(self.filters.children):
            return self.filters.children[0].render_id(session)
 
    def add_filter(self, attribute, this, that=None):
        self.table.add_filter(attribute, this, that)

    def add_column(self, col):
        self.table.add_column(col)

    def add_attribute_column(self, attr):
        return self.table.add_attribute_column(attr)

    def add_reference_filter(self, attribute, ref):
        self.table.add_reference_filter(attribute, ref)

    def insert_column(self, index, column):
        self.table.insert_column(index, column)

    def render_title(self, session):
        return self.table.render_title(session)

    def render_script(self, session):
        return ""

    def get_data_values(self, session):
        return self.table.get_data_values(session)

    def get_data_options(self, session):
        return self.table.get_data_options(session)

class ObjectSelectorTable(ObjectTable):
    def __init__(self, app, name, cls):
        super(ObjectSelectorTable, self).__init__(app, name, cls)

        self.update_enabled = True
        self.init_ids(app, cls)

    def init_ids(self, app, cls):
        item = IntegerParameter(app, "item")

        self.ids = ListParameter(app, "selection", item)
        self.add_parameter(self.ids)

        self.checkbox_column = ObjectCheckboxColumn \
            (app, "id", cls._id, self.ids)
        self.add_column(self.checkbox_column)
        
class SelectableSearchObjectTable(ObjectTable):   
    def __init__(self, app, name, cls):
        super(SelectableSearchObjectTable, self).__init__(app, name, cls)
        
    ## think about a do_process that will set up values from the URL maybe?? 
    def get_data_values(self, session):
        values = dict()

        customfield = self.parent.select_input.get(session)
        customvalue = self.parent.selectablefilters.children_by_name['search'].get(session)
        operator = self.parent.select_input.operator_param.get(session)

        #since these are added at runtime, we need to clear out the old ones each time around
        self.adapter.query.filters = [filter for filter in self.adapter.query.filters if not isinstance(filter, self.SelectableFieldFilter)]            
        if customfield is None or customvalue is None or customvalue == "":
            return values
        try:
            sql_column = self.cls._properties_by_name[customfield].sql_column
        except:
            sql_column = self.cls._statistics_by_name[customfield].sql_column

        pre = ""
        post = ""
        
        if sql_column.type.literal == "timestamp":              
            self.adapter.query.add_filter(self.SelectableFieldDateValueFilter(sql_column, customvalue))
        elif sql_column.type.literal == "int8" or sql_column.type.literal == "float8":
            if operator == ">=":
                self.adapter.query.add_filter(self.SelectableFieldValueFilter(sql_column, ">="))
            elif operator == ">":
                self.adapter.query.add_filter(self.SelectableFieldValueFilter(sql_column, ">"))
            elif operator == "<=":
                self.adapter.query.add_filter(self.SelectableFieldValueFilter(sql_column, "<="))
            elif operator == "<":
                self.adapter.query.add_filter(self.SelectableFieldValueFilter(sql_column, "<"))                    
            else:
                self.adapter.query.add_filter(self.SelectableFieldValueFilter(sql_column))
        else:
            post = "%"
            self.adapter.query.add_filter(self.SelectableFieldLikeFilter(sql_column))
        
        if not "%" in customvalue:
            pre = type == SqlLikeFilter.CONTAINS and "%%" or ""
        else:
            post = ""   
        values[customfield] = "%s%s%s" % (pre, customvalue, post)

        return values
    
    class SearchFieldOptions(OptionInputSet):
        def __init__(self, app, param):
            super(SelectableSearchObjectTable.SearchFieldOptions, self).__init__(app, "select_input", param)
                        
            self.operator_param = StringParameter(app, "operator_param")
            self.add_parameter(self.operator_param)
            
            self.operator_selector = self.SearchOperatorOptions(app, self.operator_param)
            self.add_child(self.operator_selector)
            
        def do_get_items(self, session):
            return []
    
        def render_item_value(self, session, item):
            return item.name
    
        def render_item_content(self, session, item):
            return xml_escape(item.title)
    
        def render_item_selected_attr(self, session, item):
            if item.name == self.param.get(session):
                return "selected=\"selected\""
            
        def render_onchange(self, session):
            search_box_name = self.parent.children_by_name['search'].param.path
            return "change_input_text(this, '%s');" % search_box_name   
        
        def render_item_type(self, session, item):
            return item.sql_column.type.literal     
        
        def render_select_box(self, session):
            return self.parent.children_by_name['search'].path

        class SearchOperatorOptions(OptionInputSet):
            def __init__(self, app, param):
                super(SelectableSearchObjectTable.SearchFieldOptions.SearchOperatorOptions, self).__init__(app, "operator_input", param)
                
            def do_get_items(self, session):
                return ["=", ">", ">=", "<", "<="]
    
            def render_item_value(self, session, item):
                return xml_escape(item)
    
            def render_item_content(self, session, item):
                return xml_escape(item)
    
            def render_item_selected_attr(self, session, item):
                if item == self.param.get(session):
                    return "selected=\"selected\""
                
            def render_onchange(self, session):
                return "" 

    class SelectableFieldFilter(object):
        pass
   
    class SelectableFieldLikeFilter(SqlLikeFilter, SelectableFieldFilter):
        pass
    
    class SelectableFieldValueFilter(SqlValueFilter, SelectableFieldFilter):
        pass
    
    class SelectableFieldDateValueFilter(SqlDateValueFilter, SelectableFieldFilter):
        pass        

class ObjectCheckboxColumn(ObjectTableColumn):
    def __init__(self, app, name, attr, selection):
        super(ObjectCheckboxColumn, self).__init__(app, name, attr)

        self.selection = selection

        self.header = CheckboxColumnHeader(app, "header")
        self.replace_child(self.header)

        self.cell = CheckboxColumnCell(app, "cell", selection)
        self.replace_child(self.cell)

        self.cell.input = ObjectCheckboxColumnInput(app, "input", selection)
        self.cell.replace_child(self.cell.input)

        self.sortable = False
        self.width = "25px;"

    def render_cell_value(self, session, record):
        try:
            return record[self.field.index]
        except IndexError:
            return 0

class ObjectCheckboxColumnInput(CheckboxColumnInput):
    def render_onclick_attr(self, session, record):
        value = "cumin.clickTableCheckbox(this, '%s')" % \
            self.parent.parent.selection.path

        return "onclick=\"%s\"" % value

    def render_checked_attr(self, session, record):
        if len(record) == 0:
            return ""
        checks = self.get(session)
        return record[self.parent.parent.field.index] in checks \
            and "checked=\"checked\"" or ""

class ObjectLinkColumn(ObjectTableColumn, LinkColumn):
    def __init__(self, app, name, attr, id_attr, frame_path):
        super(ObjectLinkColumn, self).__init__(app, name, attr)

        self.id_attr = id_attr
        self.frame_path = frame_path

    def init(self):
        super(ObjectLinkColumn, self).init()
 
        try:
            self.id_field = self.table.adapter.fields_by_attr[self.id_attr]
        except KeyError:
            if isinstance(self.table.adapter, ObjectQmfAdapter):
                self.id_field = ObjectQmfField(self.table.adapter, self.id_attr)
            else:
                self.id_field = ObjectSqlField(self.table.adapter, self.id_attr)

    def render_cell_href(self, session, record):
        id = record[self.id_field.index]
        frame = self.page.page_widgets_by_path[self.frame_path]

        if isinstance(frame, ObjectFrame):
            return frame.get_href(session, id)
        else:
            return frame.get_href(session, Identifiable(id)) # XXX

    def render_cell_content(self, session, record):
        return len(record) > 0 and record[self.field.index] or ""

class ObjectSelectorControl(WidgetSet):
    def do_render(self, session):
        if len(self.children):
            return super(ObjectSelectorControl, self).do_render(session)

class ObjectSelectorSwitches(ObjectSelectorControl):
    pass

class ObjectSelectorFilters(ObjectSelectorControl):
    pass

class ObjectSelectorSelectableFilters(ObjectSelectorControl):
    pass

class ObjectSelectorButtons(ObjectSelectorControl):
    pass

class ObjectSelectorLinks(ObjectSelectorControl):
    pass

class ObjectSelectorTask(ObjectTask):
    def __init__(self, app, selector):
        super(ObjectSelectorTask, self).__init__(app)

        self.cls = selector.cls

        self.selector = selector
        self.selector.tasks.append(self)

        self.form = None

    def init(self):
        super(ObjectSelectorTask, self).init()

        if not self.form:
            self.form = ObjectSelectorTaskForm(self.app, self.name, self)
            self.form.init()

    def get_title(self, session):
        pass

    def enter(self, session):
        ids = self.selector.table.ids.get(session)

        nsession = wooly.Session(self.app.form_page)

        self.form.ids.set(nsession, ids)
        self.form.return_url.set(nsession, session.marshal())
        self.form.show(nsession)

        self.do_enter(nsession, session)

        return nsession

    def do_enter(self, session, osession):
        pass

    def invoke(self, session, selection, *args):
        for item in selection:
            invoc = self.start(session, item)

            try:
                self.do_invoke(invoc, item, *args)
            except Exception, e:
                invoc.exception = e
                invoc.status = invoc.FAILED
                invoc.end()

    def do_invoke(self, invoc, item, *args):
        pass

    def get_item_content(self, session, item):
        return item.get_formatted_value("name", escape=True)

class ObjectSelectorTaskForm(FoldingFieldSubmitForm):
    def __init__(self, app, name, task):
        super(ObjectSelectorTaskForm, self).__init__(app, name)

        self.task = task

        self.cls = task.selector.cls

        item = IntegerParameter(app, "item")

        self.ids = ListParameter(app, "id", item)
        self.add_parameter(self.ids)

        self.selection = SessionAttribute(self, "selection")

        self.content = self.SelectionList(app, "fields")
        self.replace_child(self.content)

        self.app.form_page.modes.add_mode(self)

    def do_process(self, session):
        # If the selection list is zero length,
        # set cancel state and let processing complete.
        if self.get_selection(session) == 0:
            self.cancel(session)
        super(ObjectSelectorTaskForm, self).do_process(session)

    def get_selection(self, session):
        selection = list()

        self.selection.set(session, selection)

        for id in self.ids.get(session):
            try:
                item = self.cls.get_object_by_id(session.cursor, id)
                selection.append(item)
            except:
                pass
        return len(selection)

    def process_submit(self, session):
        selection = self.selection.get(session)

        self.task.invoke(session, selection)
        self.task.exit_with_redirect(session)

    def render_title(self, session):
        return self.task.get_title(session)

    class SelectionList(ItemSet):
        def do_get_items(self, session):
            return self.parent.selection.get(session)

        def render_item_content(self, session, item):
            # already escaped in get_item_content
            return self.parent.task.get_item_content(session, item)

        def render_item_class(self, session, item):
            return "item"

class MonitorSelfStatColumn(ObjectTableColumn):
    def render_header_content(self, session):
        title = self.field.get_title(session)
        parts = title.split()
        if len(parts) > 2:
            if parts[0] == "Monitor" and parts[1] == "self":
                return " ".join(parts[2:])
        return title
    
class MonitorSelfAgeColumn(ObjectTableColumn):
    def render_cell_content(self, session, record):
        value = self.field.get_content(session, record)
        days = value / 86400
        hours = (value / 3600) - (days * 24)
        minutes = (value / 60) - (days * 1440) - (hours * 60)
        return '%02d:%02d:%02d' % (days, hours, minutes)
        
class ExportButton(Widget):
    def __init__(self, app, name, args, exporter, file_name):
        super(ExportButton, self).__init__(app, name)

        self.object_attributes = list(args)
        self.file_name = file_name
        self.exporter = exporter

    def render_href(self, session):
        page = self.app.export_page
        export_session = wooly.Session(page)

        page.modes.show_child(export_session, self.exporter)
        try:
            page.set_parameters(export_session, session, self.object_attributes, self.file_name)
        except:
            return ""
        return escape_entity(export_session.marshal())

class QmfDetails(Widget):
    def __init__(self, app, name, status):
        super(QmfDetails, self).__init__(app, name)

        self.status = status

    def do_render(self, session):
        if self.status.get(session):
            return super(QmfDetails, self).do_render(session)
        return ""

    def render_details(self, session):
        status = self.status.get(session)
        return status

    def render_details_path(self, session):
        return self.parent.show_details.path

    def render_style(self, session):
        show = self.parent.show_details.get(session)
        return show and "block" or "none"

    def render_show(self, session):
        show = self.parent.show_details.get(session)
        return show and "hide" or "show"

class ObjectQmfSelector(ObjectSelector):
    def __init__(self, app, name, cls):
        super(ObjectQmfSelector, self).__init__(app, name, cls)

        self.update_enabled = True
        self.table.update_enabled = False

        self.show_details = Parameter(app, "sd")
        self.add_parameter(self.show_details)

        self.status_msg = Attribute(app, "status")
        self.add_attribute(self.status_msg)

        self.details = QmfDetails(app, "details", self.status_msg)
        self.add_child(self.details)

        self.script = self.ObjectQmfSelectorScript(app, "script")
        self.script.comments_enabled = False
        self.add_child(self.script)

        self.error_tmpl = WidgetTemplate(self, "error_html")
        self.loading_tmpl = WidgetTemplate(self, "deferred_html")

    def init(self):
        super(ObjectQmfSelector, self).init()

        assert self.get_qmf_results

    def do_render(self, session):
        tmpl = self.error_tmpl
        title = self.render_title(session)

        store = self.get_qmf_results(session)
        self.status_msg.set(session, store.status)
        error = None

        if store.exception:
            error = store.exception
            if "is unknown" in str(error):
                error = "%s are not available at this time." % title
                self.status_msg.set(session, store.exception)
        else:
            if store.status is None:
                error = "Loading"
                tmpl = self.loading_tmpl
            else:
                values = self.table.get_data_values(session)
                count = self.table.adapter.get_count(values)
                if count == 0:
                    error = "There are no %s" % title

                    if store.status == "OK":
                        details = "The call to get the data succeeded, but no results were returned."
                    else:
                        details = "The call status is <span>%s</span>" % store.status
                    self.status_msg.set(session, details)

        if error:
            writer = Writer()
            tmpl.render(writer, session, "%s" % error)
            return writer.to_string()

        return super(ObjectQmfSelector, self).do_render(session)

    def render_error_msg(self, session, msg):
        return msg

    def render_script(self, session):
        return self.script.render(session)

    class ObjectQmfSelectorScript(Widget):
        def render_table_id(self, session):
            return self.parent.table.render_id(session)

        def render_selector_id(self, session):
            return self.parent.render_id(session)

class QmfValues(Widget):
    def get_data_values(self, session):
        values = super(QmfValues, self).get_data_values(session)

        # session is needed to retrieve the qmf data
        values['session'] = session

        return values

    def get_data_options(self, session):
        options = super(QmfValues, self).get_data_options(session)

        # store the search filter in the options
        setattr(options, "like_specs", self.like_specs)

        return options

class ObjectQmfTable(QmfValues, ObjectTable):
    pass

class ObjectQmfSelectorTable(QmfValues, ObjectSelectorTable):
    pass
