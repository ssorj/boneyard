from xml.sax.saxutils import escape
from wooly import *
from wooly.tables import *
from wooly.resources import *
from wooly.parameters import *

strings = StringCatalog(__file__)

class SelectableNameColumn(ItemTableColumn):
    def __init__(self, app, name, id_param):
        super(SelectableNameColumn, self).__init__(app, name)

        self.id_param = id_param

    def render_content(self, session, object):
        id = self.get_id(object)
        name = self.get_name(object)

        selected = self.id_param.get(session) == id
        class_attr = selected and "class=\"selected\"" or ""

        branch = session.branch()
        self.id_param.set(branch, id)

        return "<a %s href=\"%s\">%s</a>" % \
            (class_attr, branch.marshal(), name)

    def get_id(self, object):
        return object.id

    def get_name(self, object):
        return self.get_id(object)

class PropertySet(ItemTable):
    def __init__(self, app, name):
        super(PropertySet, self).__init__(app, name)

        self.name_column = self.NameColumn(app, "name")
        self.add_column(self.name_column)

        self.value_column = self.ValueColumn(app, "value")
        self.add_column(self.value_column)

    def get_item_name(self, item):
        pass

    def get_item_value(self, item):
        pass

    class NameColumn(ItemTableColumn):
        def render_title(self, session, item):
            return "Name"

        def render_content(self, session, item):
            return escape(self.parent.get_item_name(item))

    class ValueColumn(ItemTableColumn):
        def render_title(self, session, item):
            return "Value"

        def render_content(self, session, item):
            return escape(self.parent.get_item_value(item))

class PanningColumnSet(Widget):
    def __init__(self, app, name):
        super(PanningColumnSet, self).__init__(app, name)

        self.start = IntegerParameter(app, "start")
        self.start.default = 0
        self.add_parameter(self.start)

        self.column_tmpl = WidgetTemplate(self, "column_html")

    def render_back_href(self, session):
        branch = session.branch()
        self.start.set(branch, max((0, self.start.get(session) - 1)))
        return branch.marshal()

    def render_columns(self, session):
        start = self.start.get(session)
        writer = Writer()

        for i, column in enumerate(self.children[start:]):
            if i > 1:
                break

            if i == 1:
                branch = session.branch()
                self.start.set(branch, start + 1)
                self.column_tmpl.render(writer, branch, column)
            else:
                self.column_tmpl.render(writer, session, column)

        return writer.to_string()

    def render_column(self, session, column):
        return column.render(session)
