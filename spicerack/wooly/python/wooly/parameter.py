from util import *

log = logging.getLogger("wooly.parameter")

class Attribute(object):
    def __init__(self, app, name):
        self.app = app
        self.name = name
        self.widget = None
        self.default = None
        self.required = True

        self.path = None

    def init(self):
        log.debug("Initializing %s", self)

        if self.widget and self.widget.path:
            self.path = ".".join((self.widget.path, self.name))
        else:
            self.path = self.name

    def seal(self):
        log.debug("Sealing %s", self)

    def validate(self, session):
        value = self.get(session)

        if value is None and self.required:
            raise Exception("%s not set" % self)

    def get(self, session):
        value = session.get(self.path)

        if value is None:
            value = self.get_default(session)

            if value is not None:
                self.set(session, value)

        return value

    def add(self, session, value, key=None):
        self.set(session, value)

    def set(self, session, value):
        session.set(self.path, value)

    def unset(self, session):
        session.unset(self.path)

    def get_default(self, session):
        return self.default

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.path)

class Parameter(Attribute):
    def __init__(self, app, name):
        super(Parameter, self).__init__(app, name)

        self.is_collection = False

    def init(self):
        super(Parameter, self).init()

        self.widget.page.init_parameter(self)

    def marshal(self, object):
        if object is None:
            string = ""
        else:
            string = self.do_marshal(object)

        return string

    def do_marshal(self, object):
        return str(object)

    def unmarshal(self, string):
        return self.do_unmarshal(string)

    def do_unmarshal(self, string):
        raise NotImplemented()
