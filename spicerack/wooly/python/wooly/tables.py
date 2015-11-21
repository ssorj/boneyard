from parameters import *
from util import *
from widgets import *
from wooly import *

strings = StringCatalog(__file__)

class ItemTable(ItemSet):
    def __init__(self, app, name):
        super(ItemTable, self).__init__(app, name)

        self.html_class = ItemTable.__name__

        self.columns = list()
        self.headers_by_column = dict()

        # which column are we sorting on
        self.scolumn = Parameter(app, "col")
        self.add_parameter(self.scolumn)

        # is sort asc
        self.reversed = BooleanParameter(app, "rev")
        self.reversed.default = False
        self.add_parameter(self.reversed)

    def get_visible_columns(self, session):
        # default impl
        return [col for col in self.columns if col.visible]

    def get_request_visible_columns(self, session, vlist):
        return [col for col in self.columns if col.visible or col.name in vlist]

    def render_headers(self, session):
        writer = Writer()

        for column in self.get_visible_columns(session):
            header = self.headers_by_column[column]
            writer.write(header.render(session))

        return writer.to_string()

    def render_column_count(self, session):
        vlist = self.get_visible_columns(session)
        return len(vlist)

    def render_cells(self, session, item):
        writer = Writer()

        for col in self.get_visible_columns(session):
            writer.write(col.render(session, item))

        return writer.to_string()

    def add_column(self, column):
        self.columns.append(column)
        self.add_child(column)

        header = column.header_class(self.app, "head", column)

        self.set_header(column, header)
        column.add_child(header)

        if self.scolumn.default is None:
            self.scolumn.default = column.name

    def render_columns(self, session):
        writer = Writer()

        for column in self.get_visible_columns(session):
            if column.width:
                writer.write("<col style=\"width: %s\"/>" % column.width)
            else:
                writer.write("<col/>")

        return writer.to_string()

    def set_header(self, column, header):
        self.headers_by_column[column] = header

    def get_selected_column(self, session):
        name = self.scolumn.get(session)
        for column in self.columns:
            if column.name == name:
                return column

    def set_default_column(self, column):
        self.scolumn.default = column.name

    def set_default_column_name(self, name):
        self.scolumn.default = name

    def is_reversed(self, session):
        return self.reversed.get(session)

    def do_get_items(self, session):
        """Gets the rows"""

        return None

    def render_count(self, session):
        count = self.get_item_count(session)
        return "%i %s" % (count, count == 1 and "item" or "items")

    def render_none(self, session):
        """For producing a message when the table is empty"""

        return None

class ItemTableColumn(Widget):
    def __init__(self, app, name):
        super(ItemTableColumn, self).__init__(app, name)

        self.header_class = ItemTableColumnHeader

        self.visible = True

        self.align = None
        self.width = None

    def get_column_key(self, session):
        return self.name

    def do_render(self, session, data):
        attrs = self.render_attrs(session)
        content = self.render_content(session, data)

        return "<td %s>%s</td>" % (attrs, content)

    def render_attrs(self, session):
        attrs = list()

        classes = self.render_class(session)

        if classes:
            attrs.append("class=\"%s\"" % classes)

        styles = self.render_style(session)

        if styles:
            attrs.append("style=\"%s\"" % styles)

        return " ".join(attrs)

    def render_style(self, session):
        if self.align:
            return "text-align: %s" % self.align

    def render_content(self, session, data):
        key = self.get_column_key(session)
        return self.render_value(session, data[key])

    def render_value(self, session, value):
        return str(value)

    # in case a non-sql column is included in an sqltable # XXX ugh
    def get_order_by_sql(self, session):
        pass

class ItemTableColumnHeader(Widget):
    def __init__(self, app, name, column):
        super(ItemTableColumnHeader, self).__init__(app, name)

        self.column = column

    def render_attrs(self, session):
        return self.column.render_attrs(session)

    def render_href(self, session):
        branch = session.branch()

        container = self.parent.parent
        sel = container.get_selected_column(session)

        if sel is self.column:
            container.reversed.set \
                (branch, not container.reversed.get(session))

        container.scolumn.set(branch, self.column.name)

        return branch.marshal()

    def render_content(self, session):
        return self.column.render_title(session)

    def render_sorted_dir(self, session):
        container = self.parent.parent
        sel = container.get_selected_column(session)

        if sel is self.column:
            if container.reversed.get(session):
                return "up"
            else:
                return "down"
        elif container.reversed.get(session):
            return "unsorted_up"
        else:
            return "unsorted_down"

class SqlTable(ItemTable):
    def __init__(self, app, name):
        super(SqlTable, self).__init__(app, name)

        self.__sql_tmpl = WidgetTemplate(self, "sql")
        self.__count_sql_tmpl = WidgetTemplate(self, "count_sql")
        self.__find_sql_tmpl = WidgetTemplate(self, "find_sql")

    def render_sql(self, session):
        writer = Writer()
        self.__sql_tmpl.render(writer, session)
        return writer.to_string()

    def render_sql_where(self, session):
        constraints = self.get_sql_where_constraints(session)

        if constraints:
            return "where %s" % " and ".join(constraints)

    def render_find_sql_where(self, session):
        pass

    def render_sql_order_by(self, session):
        scol = self.get_selected_column(session)
        if scol:
            return scol.get_order_by_sql(session)

    def render_sql_orderby(self, session):
        return self.render_sql_order_by(session)

    def render_sql_limit(self, session):
        return None

    def render_count_sql(self, session):
        writer = Writer()
        self.__count_sql_tmpl.render(writer, session)
        return writer.to_string()

    def render_find_sql(self, session):
        writer = Writer()
        self.__find_sql_tmpl.render(writer, session)
        return writer.to_string()

    def get_sql_where_constraints(self, session):
        return list()

    def get_sql_values(self, session):
        return None

    def get_find_sql_values(self, session):
        return None

    def get_connection(self, session):
        pass

    def get_item_count(self, session):
        conn = self.get_connection(session)

        if not conn:
            raise Exception("Database error")
            
        cursor = conn.cursor()
        sql = self.render_count_sql(session)
        sql_values = self.get_sql_values(session)

        cursor.execute(sql, sql_values)
        data = cursor.fetchone()

        return data[0]

    def do_get_items(self, session):
        conn = self.get_connection(session)

        if not conn:
            raise Exception("Database error")

        cursor = conn.cursor()
        sql = self.render_sql(session)
        sql_values = self.get_sql_values(session)

        #print "SQL TEXT", sql
        #print "SQL VALS", sql_values

        cursor.execute(sql, sql_values)

        return cursor

    def render_items(self, session):
        cursor = self.get_items(session)
        cols = [spec[0] for spec in cursor.description]
        data = dict()

        writer = Writer()

        for tuple in cursor:
            for col, datum in zip(cols, tuple):
                data[col] = datum

            self.item_tmpl.render(writer, session, data)

        return writer.to_string()

    def find_item(self, session):
        """ Find items in the current ItemSet

            To use this an SqlTable derived object needs to have a
            [<class>.find_sql] section and override render_find_sql_where
            and get_find_sql_values.
            Returns a list of dictionaries. Each dictionary is a matched row. """

        conn = self.get_connection(session)
        if conn:
            cursor = conn.cursor()
            select = self.render_find_sql(session)
            where = self.render_sql_where(session)
            sql_values = self.get_sql_values(session)

            find_where = self.render_find_sql_where(session)
            find_values = self.get_find_sql_values(session)
            sql = " and ".join(["%s %s" % (select, where), find_where])
            if sql_values:
                for sql_val in sql_values:
                    find_values[sql_val] = sql_values[sql_val]

            try:
                cursor.execute(sql, find_values)
                return self.cursor_to_rows(cursor)
            except Exception, e:
                pass

    def cursor_to_rows(self, cursor):
        cols = [spec[0] for spec in cursor.description]
        rows = list()

        for tuple in cursor:
            row = dict()
            for col, datum in zip(cols, tuple):
                row[col] = datum

            rows.append(row)

        return rows

class SqlTableColumn(ItemTableColumn):
    def get_order_by_sql(self, session):
        key = self.get_column_key(session)

        if key:
            dir = self.parent.is_reversed(session) and "desc" or "asc"
            return "order by %s %s" % (key, dir)

class SqlTableFilter(Widget):
    def get_sql_constraint(self, session):
        pass
