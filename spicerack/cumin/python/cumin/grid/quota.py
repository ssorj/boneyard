import logging

from negotiator import GroupHelper

from cumin.formats import fmt_link
from cumin.objectselector import ObjectQmfSelector, ObjectTableColumn,\
    ObjectQmfTable
from cumin.qmfadapter import ObjectQmfAdapter
from cumin.widgets import StaticColumnHeader
from cumin.util import xml_escape

from wooly.template import WidgetTemplate
from wooly.util import StringCatalog, Writer
from wooly import Parameter, Widget

from time import *

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.grid.quota")

class QmfGroupColumn(ObjectTableColumn):
    def __init__(self, app, name, attr, getter, negotiator, task):
        super(QmfGroupColumn, self).__init__(app, name, attr)

        self.header = StaticColumnHeader(app, "header")
        self.replace_child(self.header)

        self.title = None
        self.getter = getter
        #self.align = "right"
        self.user = False
        self.negotiator = negotiator
        self.task = task
        self.user_task = None
        self.do_escape = False

    def render_title(self, session, *args):
        return self.title

    def render_content(self, session, group):
        data = self.getter(session)
        for x in data:
            if x[0] == group:
                return self.render_data(session, x)

        return ""

    def render_data(self, session, data):
        href = self.task.get_href(session)
        content = data[2][2] and str(data[1]) or "NOT SET"
        return fmt_link(href, content, "", "", self.fmt_hover(data[0]))

    def fmt_hover(self, group):
        return "Edit the %s" % self.field.name

class StaticQmfGroupColumn(QmfGroupColumn):
    def __init__(self, app, name, attr, getter, negotiator, task):
        super(StaticQmfGroupColumn, self).__init__(app, name, attr, getter, negotiator, task)
        
    def render_header_content(self, session):
        return "Static quota"

class QuotaAdapter(ObjectQmfAdapter):
    def get_data(self, values, options):
        items = values['items']
        return items

    def get_count(self, values):
        return len(values['items'])

class QuotaTable(ObjectQmfTable):
    def __init__(self, app, name, cls):
        super(QuotaTable, self).__init__(app, name, cls)

        limit = Widget(app, "limit")
        self.header.replace_child(limit)

        page = Widget(app, "page")
        self.header.replace_child(page)

    def get_data_values(self, session):
        values = super(QuotaTable, self).get_data_values(session)

        info = self.parent.group_helper.get_config_info(session)
        expanded = self.parent.expand.get(session)

        names = list(info)
        names = sorted(names)

        # get all the values for csv export
        if session.page == self.app.export_page:
            items = names
        else:
            # make a list of groups to show based on what is expanded
            parent = expanded and self.parent.group_helper.get_parent(session, expanded) or None
            items = list()
            for name in names:
                # always show top level groups
                if "." not in name:
                    items.append(name)
                # add the current expanded item
                elif expanded == name:
                    items.append(name)
                # add the ancestors
                elif expanded and expanded.startswith(name+"."):
                    items.append(name)
                # add the direct children of expanded item
                elif expanded and name.startswith(expanded+"."):
                    sub_name = name[len(expanded) + 1:]
                    if "." not in sub_name:
                        items.append(name)
                # and direct children of expanded item's parent
                elif parent and name.startswith(parent+"."):
                    sub_name = name[len(parent) + 1:]
                    if "." not in sub_name:
                        items.append(name)

        self.parent.group_helper.get_config_for_groups(session, "GROUP_QUOTA", items)
        self.parent.group_helper.get_config_for_groups(session, "GROUP_QUOTA_DYNAMIC", items)

        values['items'] = items

        negotiator = self.parent.negotiator.get(session)
        values["obj"] = negotiator

        return values

class QuotaSelector(ObjectQmfSelector):
    def __init__(self, app, name, negotiator, frame):
        cls = app.model.com_redhat_cumin_grid.Quota

        super(QuotaSelector, self).__init__(app, name, cls)

        self.update_enabled = True
        self.table.update_enabled = False

        self.negotiator = negotiator
        self.table.negotiator = negotiator
        self.table.adapter = QuotaAdapter(app, cls)

        self.group_helper = GroupHelper(app, "groups", negotiator)
        self.add_child(self.group_helper)

        self.expand = Parameter(app, "expand")
        self.add_parameter(self.expand)

        col = self.ExpandColumn(app, "id", cls.id, self.expand, self.group_helper)
        col.header_class = StaticColumnHeader
        col.width = "20px"
        self.add_column(col)

        col = self.GroupColumn(app, "group", cls.Name)
        col.width = "70%"
        self.add_column(col)

        task = None
        col = self.StaticColumn(app, "static", cls.Quota, None, negotiator, task, self.group_helper)
        self.add_column(col)

        task = frame.edit_dynamic_quota
        col = self.DynamicColumn(app, "dynamic", cls.Quota, None, negotiator, task, self.group_helper)
        col.align = "right"
        self.add_column(col)

        self.enable_csv_export(negotiator)

    def create_table(self, app, name, cls):
        return QuotaTable(app, name, cls)

    def render_title(self, session):
        return "Quotas"

    def get_qmf_results(self, session):
        negotiator = self.negotiator.get(session)
        return self.app.model.get_negotiator_group_names(negotiator)

    class ExpandColumn(ObjectTableColumn):
        def __init__(self, app, name, attr, expand, group_helper):
            super(QuotaSelector.ExpandColumn, self).__init__(app, name, attr)

            self.expand = expand
            self.group_helper = group_helper
            self.do_escape = False

        def get_class_list(self, session):
            return ["expand"]

        def render_header_href(self, session):
            return ""

        def render_header_content(self, session):
            return ""

        def render_header_title(self, session):
            return ""

        def render_header_link_class(self, session):
            return "TableStaticColumnHeader"

        def render_cell_content(self, session, group):
            if not self.group_helper.has_child(session, group):
                return ""

            self.group_helper.get_config_info(session)
            # return a " or - depending on current expand
            expand = self.expand.get(session)
            if expand and expand.startswith(group):
                state = "-"
            else:
                state = "+"

            parent = self.group_helper.get_parent(session, group)
            return self.render_item_link(session, group, parent, state)

        def render_item_link(self, session, group, parent, state):
            branch = session.branch()

            next_expand = state == "+" and group or parent
            self.expand.set(branch, next_expand)

            hover = state == "-" and "Collapse" or "Expand"
            cls = "action"

            return fmt_link(branch.marshal(), state, class_=cls, link_title=hover)

    class GroupColumn(ObjectTableColumn):
        def __init__(self, app, name, attr):
            super(QuotaSelector.GroupColumn, self).__init__(app, name, attr)

            self.header = StaticColumnHeader(app, "header")
            self.replace_child(self.header)

            # Turn off escape in the parent because although we 
            # have to escape here, it's based on context
            self.do_escape = False

        def render_cell_content(self, session, group):
            if session.page == self.app.export_page:
                return group

            # if a user
            if "." in group:
                parts = group.split('.')
                indent = len(parts) - 1
                user = parts[indent]
                return "<span style='padding-left: %dem;'>%s</span>" %\
                    (indent, xml_escape(user))

            return xml_escape(group)

    class DynamicColumn(QmfGroupColumn):
        def __init__(self, app, name, attr, getter, negotiator, task, group_helper):
            super(QuotaSelector.DynamicColumn, self).__init__(app, name, attr, getter, negotiator, task)

            self.group_helper = group_helper
            
        def render_cell_content(self, session, group):
            value = self.group_helper.get_config_value(session, group, "GROUP_QUOTA_DYNAMIC")
            self.task.form.group_leader.set(session, group)

            try:
                fval = float(value)
            except ValueError:
                if session.page == self.app.export_page:
                    while value == self.group_helper.loading_indicator():                        
                        sleep(1)
                        value = self.group_helper.get_config_value(session, group, "GROUP_QUOTA_DYNAMIC")
                else:
                    if value == self.group_helper.loading_indicator():
                        return value
                return xml_escape(value)
            except:
                if isinstance(value, Exception):
                    content = "<span class='QuotaError'>error</span>"
                    val = len(value.args) > 0 and xml_escape(value.args[0]) or ""
                    if session.page == self.app.export_page:
                        return val
                    return fmt_link("#", content, "", "", val)

            if session.page == self.app.export_page:
                return value

            href = self.task.get_href(session)
            content = "%s%%" % str(round(fval * 100.0, 2))
            return fmt_link(href, content, "", "", self.fmt_hover(""))

        def render_text_align(self, session):
            return "right"

    class StaticColumn(StaticQmfGroupColumn):
        def __init__(self, app, name, attr, getter, negotiator, task, group_helper):
            super(QuotaSelector.StaticColumn, self).__init__(app, name, attr, getter, negotiator, task)

            self.group_helper = group_helper

        def render_cell_content(self, session, group):
            value = self.group_helper.get_config_value(session, group, "GROUP_QUOTA")

            try:
                fval = float(value)
            except ValueError:
                if session.page == self.app.export_page:
                    while value == self.group_helper.loading_indicator():                        
                        sleep(1)
                        value = self.group_helper.get_config_value(session, group, "GROUP_QUOTA")
                else:
                    if value == self.group_helper.loading_indicator():
                        return value
                return xml_escape(value)
            except:
                if isinstance(value, Exception):
                    content = "<span class='QuotaError'>error</span>"
                    val = len(value.args) > 0 and xml_escape(value.args[0]) or ""
                    if session.page == self.app.export_page:
                        return val
                    return fmt_link("#", content, "", "", val)

            if session.page == self.app.export_page:
                return value
            
            content = "%s" % str(round(fval, 2))
            return content

        def render_text_align(self, session):
            return "right"
        

