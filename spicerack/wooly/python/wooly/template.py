from util import *

class ObjectTemplate(object):
    def __init__(self, obj, text):
        self.__object = obj
        self.text = text
        self.__fragments = None

    def compile(self):
        return self.resolve(self.parse(self.text))

    def parse(self, text):
        strings = list()

        start = 0
        end = text.find("{")

        while True:
            if (end == -1):
                strings.append(text[start:])
                break

            strings.append(text[start:end])

            ccurly = text.find("}", end + 1)

            if ccurly == -1:
                start = end
                end = -1
            else:
                ocurly = text.find("{", end + 1)

                if ocurly == -1:
                    start = end
                    end = ccurly + 1
                elif ocurly < ccurly:
                    start = end
                    end = ocurly
                else:
                    strings.append("{" + text[end + 1:ccurly] + "}")

                    start = ccurly + 1
                    end = ocurly

        return strings

    def resolve(self, strings):
        fragments = list()

        for string in strings:
            if string.startswith("{") and string.endswith("}"):
                name = string[1:-1]
                method = self.find_method("render_" + name)

                if method:
                    fragments.append(method)
                else:
                    child = self.find_child(name)

                    if child:
                        fragments.append(child)
                    else:
                        fragments.append(string)
            else:
                fragments.append(string)

        return fragments

    def find_method(self, name):
        for cls in self.__object.__class__.__mro__:
            meth = getattr(cls, name, None)

            if meth and callable(meth):
                return meth

    def find_child(self, name):
        return None

    def render(self, writer, session):
        # XXX do this in an init method instead
        if not self.__fragments:
            self.__fragments = self.compile()

        for frag in self.__fragments:
            if type(frag) is str:
                writer.write(frag)
            elif callable(frag):
                #print "tc", frag, args

                try:
                    result = frag(self.__object, session)
                except TypeError, e:
                    # XXX
                    eargs = str(self), str(e)
                    raise Exception(", ".join(eargs))

                if result is not None:
                    writer.write(str(result))
            else:
                # XXX get rid of this?
                result = frag.render(session)

                if result is not None:
                    writer.write(str(result))

    def __repr__(self):
        # XXX
        #name = self.__object.__class__.__name__ + "." + self.key
        name = self.__object.__class__.__name__
        args = self.__class__.__name__, name
        return "%s('%s')" % args

class WidgetTemplate(ObjectTemplate):
    def __init__(self, widget, key):
        text = widget.get_string(key)

        if not text:
            raise Exception("Template '%s.%s' not found" \
                            % (widget.__class__.__name__, key))

        super(WidgetTemplate, self).__init__(widget, text)

        self.widget = widget

    def find_child(self, name):
        return self.widget.children_by_name.get(name)
