import struct

from wooly import *
from wooly.pages import *
from wooly.tables import *
from wooly.resources import *

from widgets import *

strings = StringCatalog(__file__)

class BasilPage(HtmlPage):
    def __init__(self, app, page):
        super(BasilPage, self).__init__(app, page)

        self.main = MainView(app, "main")
        self.add_child(self.main)

    def render_title(self, session):
        return "Basil"

class MainView(Widget):
    def __init__(self, app, name):
        super(MainView, self).__init__(app, name)

        self.tabs = TabbedModeSet(app, "tabs")
        self.add_child(self.tabs)

        objects = ObjectBrowser(app, "objects")
        self.tabs.add_tab(objects)

class ObjectBrowser(PanningColumnSet):
    def __init__(self, app, name):
        super(ObjectBrowser, self).__init__(app, name)

        self.pkgid = Parameter(app, "package")
        self.add_parameter(self.pkgid)

        self.clsid = Parameter(app, "class")
        self.add_parameter(self.clsid)

        self.objid = Parameter(app, "object")
        self.add_parameter(self.objid)

        packages = PackageSet(app, "packages", self.pkgid)
        self.add_child(packages)

        classes = ClassSet(app, "classes", self.pkgid, self.clsid)
        self.add_child(classes)

        objects = ObjectSet(app, "objects", self.clsid, self.objid)
        self.add_child(objects)

        view = ObjectView(app, "view", self.objid)
        self.add_child(view)

    def render_title(self, session):
        return "Objects"

class PackageSet(ItemTable):
    def __init__(self, app, name, pkgid):
        super(PackageSet, self).__init__(app, name)

        self.pkgid = pkgid
        
        col = self.NameColumn(app, "name", self.pkgid)
        self.add_column(col)

    def do_get_items(self, session):
        return sorted(self.app.model.packages)

    def render_title(self, session):
        return "Packages"

    class NameColumn(SelectableNameColumn):
        def get_id(self, name):
            return name

class ClassSet(ItemTable):
    def __init__(self, app, name, pkgid, clsid):
        super(ClassSet, self).__init__(app, name)

        self.pkgid = pkgid
        self.clsid = clsid

        col = self.NameColumn(app, "name", self.clsid)
        self.add_column(col)

    def do_get_items(self, session):
        id = self.pkgid.get(session)

        if id:
            try:
                classes = self.app.model.classes_by_package[id].values()
                return sorted(classes)
            except KeyError:
                pass

    def render_title(self, session):
        return "Classes"

    class NameColumn(SelectableNameColumn):
        def get_id(self, clacc):
            return clacc.getHashString()

        def get_name(self, clacc):
            name = clacc.getClassName()
            hash = "%08x" % struct.unpack("!L", clacc.getHash()[:4])
            return "%s (%s)" % (name, hash)

class ObjectSet(ItemTable):
    def __init__(self, app, name, clsid, objid):
        super(ObjectSet, self).__init__(app, name)

        self.clsid = clsid
        self.objid = objid

        col = self.NameColumn(app, "name", self.objid)
        self.add_column(col)

    def do_get_items(self, session):
        clsid = self.clsid.get(session)

        if clsid:
            objects = self.app.model.objects_by_class.get(clsid)

            if objects:
                return sorted(objects.values())

    def render_title(self, session):
        return "Classes"

    class NameColumn(SelectableNameColumn):
        def get_id(self, obj):
            return str(obj.getObjectId())

        def get_name(self, obj):
            return get_object_name(obj)

class ObjectView(Widget):
    def __init__(self, app, name, objid):
        super(ObjectView, self).__init__(app, name)

        self.objid = objid

        self.props = ObjectProperties(app, "props", self.objid)
        self.add_child(self.props)

        self.stats = ObjectStatistics(app, "stats", self.objid)
        self.add_child(self.stats)

        self.update_enabled = True

    def render_name(self, session):
        id = self.objid.get(session)

        try:
            obj = self.app.model.objects_by_id[id]
            return get_object_name(obj)
        except KeyError:
            pass

    def render_timestamp(self, session, index):
        id = self.objid.get(session)

        try:
            utime = self.app.model.objects_by_id[id].getTimestamps()[index]

            if utime != 0:
                utime = utime / float(1000000000)
                return datetime.fromtimestamp(utime)
        except KeyError:
            pass

    def render_create_time(self, session):
        return self.render_timestamp(session, 0)

    def render_update_time(self, session):
        return self.render_timestamp(session, 1)

    def render_delete_time(self, session):
        return self.render_timestamp(session, 2)

class ObjectProperties(PropertySet):
    def __init__(self, app, name, objid):
        super(ObjectProperties, self).__init__(app, name)

        self.objid = objid

    def do_get_items(self, session):
        id = self.objid.get(session)

        try:
            obj = self.app.model.objects_by_id[id]
            return obj.getProperties()
        except KeyError:
            pass

    def get_item_name(self, item):
        return shorten(item[0])

    def get_item_value(self, item):
        return shorten(item[1])

class ObjectStatistics(PropertySet):
    def __init__(self, app, name, objid):
        super(ObjectStatistics, self).__init__(app, name)

        self.objid = objid

    def do_get_items(self, session):
        id = self.objid.get(session)
        stats = self.app.model.stats_by_id.get(id)

        if stats:
            return stats.items()

    def get_item_name(self, item):
        return shorten(item[0])

    def get_item_value(self, item):
        return ", ".join([str(x) for x in reversed(item[1])])

def get_object_name(obj):
    for prop, value in obj.getProperties():
        if prop.name in ("name", "Name"):
            return value

    return shorten(obj.getIndex())

def shorten(value):
    value = str(value)

    if len(value) > 32:
        value = value[0:32] + "..."

    return value
