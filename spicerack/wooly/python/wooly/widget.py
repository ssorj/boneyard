from parameter import *
from profile import *
from template import *

log = logging.getLogger("wooly.widget")
strings = StringCatalog(__file__)

class Widget(object):
    def __init__(self, app, name):
        self.app = app
        self.name = name
        self.parent = None
        self.children = list()
        self.children_by_name = dict()
        self.attributes = list()
        self.parameters = list()

        self.sealed = False

        # Configuration
        self.html_class = None
        self.update_enabled = False

        # These are computed later in the init pass
        self.ancestors = None
        self.path = None
        self.page = None
        self.frame = None

        self.__main_tmpl = WidgetTemplate(self, "html")

    def init(self):
        log.debug("Initializing %s" % self)

        self.init_computed_values()

        if self.page:
            self.page.init_widget(self)

        for attr in self.attributes:
            attr.init()

        for param in self.parameters:
            param.init()

        for child in self.children:
            child.init()

    def init_computed_values(self):
        ancestors = list()
        widget = self.parent

        while widget is not None:
            ancestors.append(widget)
            widget = widget.parent

        self.ancestors = tuple(ancestors)

        pelems = [x.name for x in reversed(ancestors)]
        pelems.append(self.name)
        self.path = ".".join(pelems[1:])

        self.page = self.ancestors[-1]

        for widget in ancestors:
            if isinstance(widget, Frame):
                self.frame = widget
                break

        if not self.html_class:
            self.init_html_class()

    def init_html_class(self):
        tokens = list()

        if self.page.page_html_class:
            tokens.append(self.page.page_html_class)

        for cls in self.__class__.__mro__:
            tokens.append(cls.__name__)

            if cls is Widget:
                break

        if not tokens:
            tokens.append("_")

        self.html_class = " ".join(tokens)

    def seal(self):
        assert not self.sealed
        self.sealed = True

        assert self.path is not None, self
        # XXX produces an import error
        #assert isinstance(self.page, Page), self.page

        for attr in self.attributes:
            attr.seal()

        for param in self.attributes:
            param.seal()

        for child in self.children:
            child.seal()

    def add_child(self, child):
        assert not self.sealed, self
        assert isinstance(child, Widget), (self, child)
        assert child is not self, self
        assert child not in self.children, (self, child, self.children)
        assert child.name not in self.children_by_name, child.name

        self.children.append(child)
        self.children_by_name[child.name] = child
        child.parent = self

    def remove_child(self, child):
        assert not self.sealed
        assert isinstance(child, Widget)
        assert child is not self

        self.children.remove(child)
        del self.children_by_name[child.name]
        child.parent = None

    def replace_child(self, child):
        existing = self.children_by_name.get(child.name)

        if existing:
            self.remove_child(existing)

        self.add_child(child)

    def add_attribute(self, attribute):
        assert not self.sealed
        assert isinstance(attribute, Attribute)

        self.attributes.append(attribute)
        attribute.widget = self

    def add_parameter(self, parameter):
        assert not self.sealed
        assert isinstance(parameter, Parameter)

        self.parameters.append(parameter)
        parameter.widget = self

    def get_ancestor(self, name):
        for anc in self.ancestors:
            if anc.name == name:
                return anc

    @classmethod
    def get_module_strings(cls):
        module = sys.modules[cls.__module__]
        return module.__dict__.get("strings")

    def get_string(self, key):
        for cls in self.__class__.__mro__:
            if cls is object:
                return

            str = None
            strs = cls.get_module_strings()

            if strs:
                str = strs.get(cls.__name__ + "." + key)

                if str:
                    return str

            str = cls.__dict__.get(key)

            if str:
                return str

    def show(self, session):
        assert self.parent

        self.parent.show_child(session, self)
        self.parent.show(session)

        return self

    def show_child(self, session, child):
        pass

    def save_parameters(self, session, params):
        params.extend(self.parameters)

        for child in self.children:
            child.save_parameters(session, params)

    def process(self, session):
        if self.update_enabled:
            self.page.enable_update(session, self)

        if self.app.debug:
            profile = self.page.profile.get(session)

            call = ProcessCall(profile, self, None)
            call.do(session)
        else:
            self.do_process(session)

    def do_process(self, session):
        for child in self.children:
            child.process(session)

    def get_title(self, session):
        pass

    def render(self, session):
        try:
            if self.app.debug:
                profile = self.page.profile.get(session)

                call = RenderCall(profile, self, None)
                string = call.do(session)
            else:
                string = self.do_render(session)
        except TypeError, e:
            # XXX
            eargs = str(self), str(e)
            raise Exception(", ".join(eargs))

        if string is None:
            string = ""

        return string

    def do_render(self, session):
        writer = Writer()
        self.__main_tmpl.render(writer, session)
        return writer.to_string()

    def render_id(self, session):
        return self.path

    def render_class(self, session):
        return self.html_class

    def render_href(self, session):
        return session.marshal()

    def render_title(self, session):
        return self.get_title(session)

    def render_resource_prefix(self, session):
        return self.page.get_resource_prefix(session)

    def render_content(self, session):
        writer = Writer()

        for child in self.children:
           writer.write(child.render(session))

        return writer.to_string()

    def __repr__(self):
        args = self.__class__.__module__, self.__class__.__name__, self.path
        return "%s.%s('%s')" % args

class Frame(Widget):
    def show(self, session):
        super(Frame, self).show(session)

        return self.page.set_frame(session, self)

    def save_parameters(self, session, params):
        frame = self.page.get_frame(session)

        if self is frame or self in frame.ancestors:
            super(Frame, self).save_parameters(session, params)
