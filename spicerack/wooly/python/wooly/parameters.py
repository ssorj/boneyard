from util import *
from wooly import *

class ListParameter(Parameter):
    def __init__(self, app, name, item_parameter):
        super(ListParameter, self).__init__(app, name)

        self.item_parameter = item_parameter
        self.default = list()

        self.is_collection = True

    def get_default(self, session):
        return copy(self.default)

    def add(self, session, value, key=None):
        lst = self.get(session)
        lst.append(value)
        return lst

    def do_unmarshal(self, string):
        return self.item_parameter.do_unmarshal(string)

    def do_marshal(self, object):
        return self.item_parameter.do_marshal(object)

class StringParameter(Parameter):
    def do_unmarshal(self, string):
        return string

# XXX this will be a strict sort of string parameter
class SymbolParameter(StringParameter):
    pass

class IntegerParameter(Parameter):
    def do_unmarshal(self, string):
        try:
            return int(string)
        except:
            return string

class FloatParameter(Parameter):
    def do_unmarshal(self, string):
        try:
            return float(string)
        except:
            return string

class BooleanParameter(Parameter):
    def __init__(self, app, name):
        super(BooleanParameter, self).__init__(app, name)

        self.default = False

    def do_unmarshal(self, string):
        return string == "t"

    def do_marshal(self, object):
        return object and "t" or "f"

class VoidBooleanParameter(Parameter):
    def get(self, session):
        return self.path in session.values_by_path

    def set(self, session, value):
        key = self.path

        if value:
            session.set(key, None)
        else:
            session.unset(key)

class PageParameter(Parameter):
    def __init__(self, app, name):
        super(PageParameter, self).__init__(app, name)

    def do_unmarshal(self, string):
        return self.app.pages_by_name.get(string)

    def do_marshal(self, page):
        return page.name
