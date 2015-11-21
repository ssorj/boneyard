from parameters import *
from table import *
from util import *
from widgets import *
from wooly import *

strings = StringCatalog(__file__)

class DataAdapter(object):
    def __init__(self):
        self.fields = list()
        self.fields_by_name = dict()

    def init(self):
        for field in self.fields:
            field.init()

    def get_count(self):
        pass

    def get_sort_limit(self):
        return None

    def get_data(self, values, options):
        return ()

class DataAdapterField(object):
    def __init__(self, adapter, name, type):
        self.adapter = adapter
        self.name = name
        self.type = type
        self.format = None

        self.index = len(self.adapter.fields)
        self.adapter.fields.append(self)
        self.adapter.fields_by_name[self.name] = self

    def init(self):
        if self.format is None and self.type is float:
            self.format = "%0.02f"

    def get_title(self, session):
        pass

    def get_content(self, session, record):
        value = record[self.index]

        if self.format is not None:
            if callable(self.format):
                value = self.format(value)
            elif value is not None:
                try:
                    value = self.format % value
                except:
                    value = "Error"

        return value

    def __repr__(self):
        args = (self.__class__.__name__, self.name, self.type.__name__)
        return "%s(%s,%s)" % args

class DataAdapterOptions(object):
    def __init__(self):
        self.sort_field = None
        self.sort_ascending = True
        self.limit = None
        self.offset = None

        self.attributes = dict()

class DataTable(Table):
    def __init__(self, app, name):
        super(DataTable, self).__init__(app, name)

        self.adapter = None

        self.data = Attribute(app, "data")
        self.add_attribute(self.data)

        self.summary = Attribute(app, "summary")
        self.add_attribute(self.summary)

        self.count = Attribute(app, "count")
        self.add_attribute(self.count)

        self.header = DataTableHeader(app, "header")
        self.replace_child(self.header)

        self.footer = DataTableFooter(app, "footer")
        self.replace_child(self.footer)

    def init(self):
        super(DataTable, self).init()

        assert isinstance(self.adapter, DataAdapter), self.adapter
        self.adapter.init()

    def get_data(self, session):
        values = self.get_data_values(session)
        options = self.get_data_options(session)

        return self.adapter.get_data(values, options)

    def get_data_values(self, session):
        return {}

    def get_data_options(self, session):
        options = DataAdapterOptions()

        name = self.sort.get(session)

        if name:
            column = self.children_by_name[name]

            if hasattr(column, "field"):
                options.sort_field = column.field

        options.sort_ascending = self.ascending.get(session)
        options.limit = self.header.limit.get(session)
        options.offset = self.header.offset.get(session)

        # make sure offset is a multiple of limit
        # this happens sometimes when we change limits
        if options.offset % options.limit:
            options.offset = (options.offset / options.limit) * options.limit
            self.header.offset.set(session, options.offset)

        return options

    def get_count(self, session):
        values = self.get_data_values(session)
        return self.adapter.get_count(values)

    def do_render(self, session):
        start = time.time()

        data = self.get_data(session)

        seconds = time.time() - start

        self.data.set(session, data)
        self.summary.set(session, (len(data), seconds))
        self.count.set(session, self.get_count(session))

        return super(DataTable, self).do_render(session)

    def render_font_size(self, session):
        return "%.1fem" % self.header.font.get(session)

    def render_css(self, session):
        writer = Writer()

        font = self.header.font.get(session)
        writer.write("table.DataTable { font-size: %.1fem; }" % font)

        for column in self.get_visible_columns(session):
            writer.write(column.css.render(session))

        return writer.to_string()

    def render_rows(self, session):
        data = self.data.get(session)

        writer = Writer()

        for record in data:
            writer.write(self.row.render(session, record))

        return writer.to_string()

    def render_footer_options(self, session):
        return None

class DataTableColumn(TableColumn):
    def __init__(self, app, name):
        super(DataTableColumn, self).__init__(app, name)

        self.field = None

    def render_text_align(self, session):
        if self.field.type in (long, int, float, complex):
            return "right"

        return "left"

    def render_header_content(self, session):
        return self.field.get_title(session)

    def render_cell_content(self, session, record):
        return self.field.get_content(session, record)
    
    def render_cell_title(self, session, record):
        return ""

class DataTableHeader(TableHeader):
    def __init__(self, app, name):
        super(DataTableHeader, self).__init__(app, name)

        self.font = FloatParameter(app, "font")
        self.font.default = 0.9
        self.add_parameter(self.font)

        self.limit = IntegerParameter(app, "limit")
        self.limit.default = 25
        self.add_parameter(self.limit)

        self.offset = IntegerParameter(app, "offset")
        self.offset.default = 0
        self.add_parameter(self.offset)

        self.font_selector = DataTableFontSelector(app, "font", self.font)
        self.add_child(self.font_selector)

        self.limit_selector = DataTableLimitSelector(app, "limit", self.limit)
        self.add_child(self.limit_selector)

        self.page_selector = DataTablePageSelector(app, "page", self.offset)
        self.add_child(self.page_selector)

class DataTableFooter(TableFooter):
    def render_summary(self, session):
        results, seconds = self.table.summary.get(session)
        count = self.table.count.get(session)

        args = (results, count)
        return "%i of %i" % args
        #args = (results, count, seconds * 1000)
        #return "%i of %i, %.02f millis" % args

    def render_options(self, session):
        return self.parent.render_footer_options(session)

class DataTableSelector(TableChild):
    def __init__(self, app, name, selection):
        super(DataTableSelector, self).__init__(app, name)

        self.selection = selection

        self.option = self.Option(app, "option")
        self.add_child(self.option)

    def get_options(self, session):
        return ()

    def render_options(self, session):
        options = list()

        for option in self.get_options(session):
            options.append(self.option.render(session, option))

        return ", ".join(options)

    class Option(Link):
        def render_class(self, session, option):
            if self.parent.selection.get(session) == option[0]:
                return "selected"

        def render_title(self, session, option):
            return option[2]

        def edit_session(self, session, option):
            self.parent.selection.set(session, option[0])

        def render_content(self, session, option):
            return option[1]

class DataTableFontSelector(DataTableSelector):
    def get_options(self, session):
        return ((0.8, "S", "Small"), (0.9, "M", "Medium"), (1.0, "L", "Large"))

    def render_title(self, session):
        return "Font"

class DataTablePageSelector(DataTableSelector):
    max_page_links = 16

    def get_options(self, session):
        # number of items in the table
        count = self.table.count.get(session)
        if not count:
            return []

        # number of items per page
        limit = self.table.header.limit.get(session)

        # info for each possible page of results
        options = [(x[1], x[0] + 1, "Goto page %i" % (x[0] + 1, )) for x in enumerate(range(0, count, limit))]

        # the starting item on the current page
        selection = self.selection.get(session)

        #find the index of the current page
        cur_page = 0
        for page in options:
            if selection == page[0]:
                cur_page = page[1] - 1
                break

        pages = list()

        # adjust the page links shown so that the current page is in the list
        first_page = max(cur_page - 1, 0)
        last_page = min(first_page + self.max_page_links, len(options))
        first_page = max(last_page - self.max_page_links, 0)

        if first_page:
            pages.append((0, "First", "First page"))
            prev = max(selection - limit, 0)
            pages.append((prev, "Prev", "Previous page"))

        pages.extend(options[first_page : last_page])

        if last_page < len(options):
            next = options[cur_page + 1][0]
            pages.append((next, "Next", "Next page"))

            last = options[len(options) - 1][0]
            pages.append((last, "Last", "Last page"))

        return pages

    def render_title(self, session):
        return self.table.count.get(session) and "Page" or ""

class DataTableLimitSelector(DataTableSelector):
    def get_options(self, session):
        return ((25, 25, "25 items per page"), (50, 50, "50 items per page"), (100, 100, "100 items per page"))

    def render_title(self, session):
        return "Limit"
