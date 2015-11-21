from parameters import *
from resources import *
from util import *
from wooly import *

strings = StringCatalog(__file__)

class ModeSet(Widget):
    def __init__(self, app, name):
        super(ModeSet, self).__init__(app, name)

        self.modes = list()

        self.mode = self.ModeParameter(app, "m")
        self.add_parameter(self.mode)

    def add_mode(self, mode):
        self.modes.append(mode)

        super(ModeSet, self).add_child(mode)

        if not self.mode.default:
            self.mode.default = mode

    def show_child(self, session, child):
        self.mode.set(session, child)

    def do_process(self, session):
        mode = self.mode.get(session)
        mode.process(session)

    def render_content(self, session):
        mode = self.mode.get(session)
        return mode.render(session)

    class ModeParameter(Parameter):
        def do_marshal(self, mode):
            return mode.name

        def do_unmarshal(self, name):
            try:
                return self.widget.children_by_name[name]
            except KeyError:
                pass

class Link(Widget):
    def edit_session(self, session):
        pass

    def render_href(self, session):
        branch = session.branch()
        self.edit_session(branch)
        return branch.marshal()

    def render_title(self, session):
        return ""

class Toggle(Link):
    def __init__(self, app, name):
        super(Toggle, self).__init__(app, name)

        self._enabled = BooleanParameter(app, "enabled")
        self.add_parameter(self._enabled)

    def is_enabled(self, session):
        return self._enabled.get(session)

    def set_enabled(self, session, enabled):
        self._enabled.set(session, enabled)

    def do_process(self, session):
        if self.is_enabled(session):
            self.on_click(session)

    def on_click(self, session):
        pass

    def render_href(self, session):
        branch = session.branch()
        self.set_enabled(branch, not self.is_enabled(session))
        return branch.marshal()

    def render_state(self, session):
        return self.is_enabled(session) and "on" or "off"

class ItemSet(Widget):
    def __init__(self, app, name, item_widget):
        super(ItemSet, self).__init__(app, name)

        assert isinstance(item_widget, ItemWidget), item_widget

        self.item_widget = item_widget
        self.add_child(self.item_widget)

        self.selection = Attribute(app, "selection")
        self.add_attribute(self.selection)

    def get_item_count(self, session):
        return len(self.get_items(session))

    def get_items(self, session):
        items = self.do_get_items(session)

        if items is None:
            items = ()

        return items

    def do_get_items(self, session):
        pass

    def render_items(self, session):
        writer = Writer()

        for item in self.get_items(session):
            self.item_widget.item.set(session, item)

            if item is selected_item:
                self.item_widget.selected.set(session, True)

            writer.write(self.item_widget.render(session))

        return writer.to_string()

class ItemWidget(Widget):
    def __init__(self, app, name):
        super(ItemWidget, self).__init__(app, name)

        self.item = Attribute(app, "item")
        self.add_attribute(self.item)

        self.selected = Attribute(app, "selected")
        self.add_attribute(self.selected)

    def init(self):
        super(ItemWidget, self).init()

        assert isinstance(self.parent, ItemSet), self.parent

    def is_selected(self, session):
        item = self.item.get(session)
        selection = self.parent.selection.get(session)

        return item is selection    

    def render_class(self, session):
        if self.is_selected(session):
            return "selected"
        else:
            return "_"

    # XXX use item.show below? XXXXXXXXXX

    def render_href(self, session, item):
        branch = session.branch()
        item = self.item.get(session)

        self.parent.selection.set(branch, item)

        return branch.marshal()

class TabSet(ModeSet):
    def __init__(self, app, name):
        super(TabSet, self).__init__(app, name)

        self.links = TabSetLinks(app, "links")
        self.add_child(self.links)

    def add_tab(self, tab):
        self.add_mode(tab)

    def render_tabs(self, session):
        writer = Writer()

        for tab in self.__tabs:
            self.__tab_tmpl.render(writer, session, tab)

        return writer.to_string()

class TabSetLinkSet(ItemSet):
    def __init__(self, app, name):
        item_widget = TabSetLinkWidget(app, "link")
        super(TabSetLinkSet, self).__init__(app, name, item_widget)

class TabSetLinkWidget(ItemWidget):
    def render_href(self, session):
        tab = self.item.get(session)

        branch = session.branch()
        tab.show(branch)

        return branch.marshal()

    def render_content(self, session, tab):
        return tab.get_title(session)

# class RadioModeSet(TabbedModeSet):
#     """ exists just to provide different class/styles """
#     pass

# class RenderingItemSet(Widget):
#     def __init__(self, app, name, item_renderer):
#         super(RenderingItemSet, self).__init__(app, name)

#         self.item_renderer = item_renderer

#         self.items = Attribute(app, "items")
#         self.add_attribute(self.items)

#     def get_item_count(self, session):
#         return len(self.get_items(session))

#     def get_items(self, session):
#         items = self.items.get(session)

#         if items is None:
#             items = self.do_get_items(session)

#             if items is None:
#                 items = ()

#         return items

#     def do_get_items(self, session):
#         pass

#     def render_items(self, session):
#         writer = Writer()

#         for item in self.get_items(session):
#             self.item_renderer.render(writer, session, item)

#         return writer.to_string()

# class ItemRenderer(object):
#     def __init__(self, widget):
#         self.widget = widget

#     def render_content(self, session, item):
#         return item

#     def render(self, writer, session, item):
#         return self.render_content(session, item)

# class TemplateRenderer(ItemRenderer):
#     def __init__(self, widget, template_key):
#         super(TemplateRenderer, self).__init__(widget)

#         text = self.widget.get_string(template_key)
#         self.__tmpl = ObjectTemplate(self, text)

#     def render(self, writer, session, item):
#         self.__tmpl.render(writer, session, item)

# class ItemTree(ItemSet):
#     def get_items(self, session):
#         """Get the root items"""
#         pass

#     def get_child_items(self, session):
#         pass

#     def render_child_items(self, session):
#         writer = Writer()

#         for child in self.get_child_items(session):
#             self.item_renderer.render(writer, session, child)

#         return writer.to_string()

# class Paginator(RenderingItemSet):
#     def __init__(self, app, name):
#         renderer = self.PageLink(self, "page_html")
#         super(Paginator, self).__init__(app, name, renderer)

#         self.page_index = IntegerParameter(app, "page")
#         self.page_index.default = 0
#         self.add_parameter(self.page_index)

#         self.pageset_index = IntegerParameter(app, "pageset")
#         self.pageset_index.default = 0
#         self.add_parameter(self.pageset_index)

#         self.page_count = Attribute(app, "count")
#         self.add_attribute(self.page_count)

#         self.page_size = 14
#         self.pageset_size = 5

#     def get_bounds(self, session):
#         page = self.page_index.get(session)
#         return self.page_size * page, self.page_size * (page + 1)

#     def get_pageset_bounds(self, session):
#         pageset = self.pageset_index.get(session)
#         return self.pageset_size * pageset, self.pageset_size * (pageset + 1)

#     def set_count(self, session, count):
#         page_index = self.page_index.get(session)
#         pageset_index = self.pageset_index.get(session)
#         count_per_pageset = self.page_size * self.pageset_size

#         # is the count too low to be on the current pageset
#         if count < count_per_pageset * pageset_index:
#             self.pageset_index.set(session, 0)
#             self.page_index.set(session, 0)

#         # is the count too low to be on the current page
#         elif count < page_index * self.page_size:
#             self.pageset_index.set(session, 0)
#             self.page_index.set(session, 0)

#         return self.page_count.set(session, count)

#     def get_count(self, session):
#         return self.page_count.get(session)

#     def get_page_count(self, session):
#         count = self.get_count(session)
#         return int(math.ceil(count / float(self.page_size)))

#     def get_pageset_count(self, session):
#         page_count = self.get_page_count(session)
#         return int(math.ceil(page_count / float(self.pageset_size)))

#     def __link(self, href, content, class_=""):
#         return "<a href=\"%s\"%s>%s</a>" % \
#             (href, class_ and " class=\"%s\" " % class_ or " ", content)

#     def render_prev_page_link(self, session):
#         page = self.page_index.get(session)

#         if page < 1:
#             html = self.__link(session.marshal(), "&lt;", "pagenav disabled")
#         else:
#             page -= 1
#             pageset_start = self.get_pageset_bounds(session)[0]

#             branch = session.branch()
#             self.page_index.set(branch, page)
#             if page < pageset_start:
#                 nindex = self.pageset_index.get(session) - 1
#                 self.pageset_index.set(branch, nindex)
#             html = self.__link(branch.marshal(), "&lt;", "pagenav")

#         return html

#     def render_next_page_link(self, session):
#         page = self.page_index.get(session)

#         if page >= self.get_page_count(session) - 1:
#             html = self.__link(session.marshal(), "&gt;", "pagenav disabled")
#         else:
#             page += 1
#             pageset_end = self.get_pageset_bounds(session)[1]

#             branch = session.branch()
#             self.page_index.set(branch, page)
#             if page >= pageset_end: # XXX should be >? bounds func is funny
#                 nindex = self.pageset_index.get(session) + 1
#                 self.pageset_index.set(branch, nindex)
#             html = self.__link(branch.marshal(), "&gt;", "pagenav")

#         return html

#     def render_prev_pageset_link(self, session):
#         pageset = self.pageset_index.get(session)

#         if pageset < 1:
#             html = self.__link(session.marshal(), "&lt;&lt;", "pagenav disabled")
#         else:
#             page_index = self.page_index.get(session)
#             branch = session.branch()
#             self.pageset_index.set(branch, pageset - 1)
#             self.page_index.set(branch, page_index - self.pageset_size)
#             html = self.__link(branch.marshal(), "&lt;&lt;", "pagenav")

#         return html

#     def render_next_pageset_link(self, session):
#         pageset = self.pageset_index.get(session)

#         if pageset >= self.get_pageset_count(session) - 1:
#             html = self.__link(session.marshal(), "&gt;&gt;", "pagenav disabled")
#         else:
#             branch = session.branch()
#             self.pageset_index.set(branch, pageset + 1)
#             new_page_index = self.page_index.get(branch) + self.pageset_size
#             max_page_count = self.get_page_count(branch)
#             if new_page_index >= max_page_count:
#                 new_page_index = max_page_count - 1
#             self.page_index.set(branch, new_page_index)
#             html = self.__link(branch.marshal(), "&gt;&gt;", "pagenav")

#         return html

#     def do_get_items(self, session):
#         count = self.page_count.get(session)

#         start, end = self.get_pageset_bounds(session)
#         page_count = self.get_page_count(session)

#         return range(start, min(end, page_count))

#     class PageLink(TemplateRenderer):
#         def render_class_attr(self, session, page):
#             if self.widget.page_index.get(session) == page:
#                 return " class=\"selected\""

#         def render_href(self, session, page):
#             branch = session.branch()
#             self.widget.page_index.set(branch, page)
#             return branch.marshal()

#         def render_content(self, session, page):
#             return page + 1

# class PropertySet(RenderingItemSet):
#     def __init__(self, app, name, item_renderer=None):
#         super(PropertySet, self).__init__(app, name, item_renderer)

#         if self.item_renderer is None:
#             self.item_renderer = PropertyRenderer(self, "property_html")

# class PropertyRenderer(TemplateRenderer):
#     def render_title(self, session, prop):
#         return escape_amp(prop[0])

#     def render_value(self, session, prop):
#         value = prop[1]
#         try:
#             escapable = prop[2]
#         except IndexError:
#             escapable = True

#         if type(value) is str and escapable:
#             if len(value) > 30:
#                 value = value[:30] + "..."

#             value = escape(value)
#         elif value is None:
#             value = "<em>None</em>"

#         return value
