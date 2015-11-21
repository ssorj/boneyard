from forms import *
from parameters import *
from util import *
from wooly import *

strings = StringCatalog(__file__)

class Table(Widget):
    def __init__(self, app, name):
        super(Table, self).__init__(app, name)

        self.header = TableHeader(app, "header")
        self.add_child(self.header)

        self.footer = TableFooter(app, "footer")
        self.add_child(self.footer)

        self.columns = list()

        self.row = TableRow(app, "row")
        self.add_child(self.row)

        self.sort = SymbolParameter(app, "sort")
        self.add_parameter(self.sort)

        self.ascending = BooleanParameter(app, "ascending")
        self.add_parameter(self.ascending)

    def get_ascending_by_type(self, the_type):
        # Override this method to do something special
        # for a particular table
        return the_type not in (int, float, long, complex)

    def set_default_sort_column(self, column):
        # Save a reference to the column so that we
        # can determine type once it's initialized
        self.sort.default = column.name
        self._sort_col = column

    def set_default_sort_direction(self):
        if self._sort_col:
            self.ascending.default = \
                    self.get_ascending_by_type(self._sort_col.field.type)
            
    def add_column(self, column):
        self.add_child(column)

        self.columns.append(column)

    def insert_column(self, index, column):
        self.add_child(column)

        self.columns.insert(index, column)

    def get_data(self, session):
        return ()

    def get_visible_columns(self, session):
        return [x for x in self.columns if x.visible]

    def render_css(self, session):
        writer = Writer()

        for column in self.get_visible_columns(session):
            writer.write(column.css.render(session))

        return writer.to_string()

    def render_columns(self, session):
        writer = Writer()

        for column in self.get_visible_columns(session):

            writer.write(column.render(session))

        return writer.to_string()

    def render_colspan(self, session):
        return len(self.get_visible_columns(session))

    def render_rows(self, session):
        data = self.get_data(session)

        writer = Writer()

        for record in data:
            writer.write(self.row.render(session, record))

        return writer.to_string()

class TableChild(Widget):
    def init(self):
        super(TableChild, self).init()

        for anc in self.ancestors:
            if isinstance(anc, Table):
                self.table = anc

        assert self.table, "Not inside a table"

class TableColumn(TableChild):
    def __init__(self, app, name):
        super(TableColumn, self).__init__(app, name)

        self.css = TableColumnCss(app, "css")
        self.add_child(self.css)

        self.header = TableColumnHeader(app, "header")
        self.add_child(self.header)

        self.cell = TableColumnCell(app, "cell")
        self.add_child(self.cell)

        self.sortable = True
        self.visible = True
        self.width = None
        self.static_header = False
        self.do_escape = True

    def render_class(self, session):
        tokens = list()
        tokens.append(self.name)

        if self.name == self.table.sort.get(session):
            tokens.append("selected")

        return " ".join(tokens)

    def render_width(self, session):
        width = self.width

        if not width:
            width = "auto"

        return width

    def render_text_align(self, session):
        return "left"
    
    def render_header_href(self, session):
        # For the current sort column, just invert the sort order.
        # For other columns, set initial sort order based type
        sort = self.table.sort.get(session)
        if sort == self.name:
            ascending = not self.table.ascending.get(session)
        else:
            ascending = self.table.get_ascending_by_type(self.field.type)

        branch = session.branch()
        self.table.sort.set(branch, self.name)
        self.table.ascending.set(branch, ascending)
        return branch.marshal()

    def render_header_title(self, session):
        # For the current sort column, just invert the sort order.
        # For other columns, set initial sort order based type
        sort = self.table.sort.get(session)
        if sort == self.name:
            ascending = self.table.ascending.get(session)
            dir = ascending and "descending" or "ascending"
        else:
            ascending = self.table.get_ascending_by_type(self.field.type)
            dir = ascending and "ascending" or "descending" 
        name = self.render_header_content(session)
        if not name:
            name = self.name

        return "Click to sort in %s order by %s" % (dir, name)

    def render_header_content(self, session):
        pass

    def render_header_link_class(self, session):
        pass

    def do_render_cell_content(self, session, record):
        r = self.render_cell_content(session, record)
        if self.do_escape:
            return xml_escape(r)
        return r

    def render_cell_content(self, session, record):
        pass

    def do_render_cell_title(self, session, record):
        r = self.render_cell_title(session, record)
        if self.do_escape:
            return xml_escape(r)
        return r

    def render_cell_title(self, session, record):
        pass
    
class TableColumnCss(TableChild):
    def __init__(self, app, name):
        super(TableColumnCss, self).__init__(app, name)

        # html comments in the css freaks out webkit browsers
        self.comments_enabled = False

    def render_class(self, session):
        return self.parent.name

    def render_text_align(self, session):
        return self.parent.render_text_align(session)

    def render_width(self, session):
        return self.parent.render_width(session)

class TableColumnHeader(TableChild):
    def __init__(self, app, name):
        super(TableColumnHeader, self).__init__(app, name)

        self.static_tmpl = WidgetTemplate(self, "static_html")

    def do_render(self, session, *args):
        if self.parent.static_header or (self.table.adapter.get_sort_limit() is not None and self.table.count.get(session) > self.table.adapter.get_sort_limit()):
            writer = Writer()
            self.static_tmpl.render(writer, session)
            return writer.to_string()

        return super(TableColumnHeader, self).do_render(session, *args)

    def render_class(self, session):
        cls = self.parent.render_class(session)
        align = self.parent.render_text_align(session)
        if align is "right":
            return " ".join(("ralign", cls))
        return cls

    def render_link_class(self, session):
        return self.parent.render_header_link_class(session)

    def render_href(self, session):
        return self.parent.render_header_href(session)

    def render_content(self, session):
        return self.parent.render_header_content(session)

    def render_sorted_dir(self, session):
        container = self.table
        sel = container.sort.get(session)
        asc = container.ascending.get(session)
        if sel == self.parent.name:
            if asc:
                return "up"
            else:
                return "down"
        elif asc:
            return "unsorted_up"
        else:
            return "unsorted_down"

    def render_title(self, session):
        return self.parent.render_header_title(session)

class TableColumnCell(TableChild):
    def render_class(self, session, record):
        return self.parent.render_class(session)

    def render_content(self, session, record):
        return self.parent.do_render_cell_content(session, record)
    
    def render_cell_title(self, session, record):
        #gives us the title="" attribute for each table cell
        return self.parent.do_render_cell_title(session, record)

class TableHeader(TableChild):
    def render_colspan(self, session):
        return self.table.render_colspan(session)

    def render_headers(self, session):
        writer = Writer()

        for column in self.table.get_visible_columns(session):
            if self.app.authorize_cb(session, column):
                writer.write(column.header.render(session))

        return writer.to_string()

class TableFooter(TableChild):
    def render_colspan(self, session):
        return self.table.render_colspan(session)

class TableRow(TableChild):
    def render_cells(self, session, record):
        writer = Writer()

        for column in self.table.get_visible_columns(session):
            if self.app.authorize_cb(session, column):
                writer.write(column.cell.render(session, record))

        return writer.to_string()

class LinkColumn(TableColumn):
    def __init__(self, app, name):
        super(LinkColumn, self).__init__(app, name)

        self.cell = LinkColumnCell(app, "cell")
        self.replace_child(self.cell)

    def render_cell_href(self, session, record):
        pass

class LinkColumnCell(TableColumnCell):
    def render_href(self, session, record):
        return self.parent.render_cell_href(session, record)

class CheckboxColumnHeader(TableColumnHeader):
    def render_name(self, session):
        return self.parent.selection.path

class CheckboxColumnCell(TableColumnCell):
    def __init__(self, app, name, selection):
        super(CheckboxColumnCell, self).__init__(app, name)

        self.input = CheckboxColumnInput(app, "input", selection)
        self.add_child(self.input)

    def render_content(self, session, record):
        return self.input.render(session, record)

class CheckboxColumnInput(CheckboxInput):
    def render_value(self, session, record):
        return self.parent.parent.render_cell_value(session, record)
