#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

"""
Classes for rendering objects bound to templates

A render object has one or more templates.  Templates contain
placeholders delimited by curly braces::

    <h1>{title}</h1>

When an object is rendered, each placeholder is replaced by a call to
a corresponding render method::

    def render_title(self, request):
        return "Index"
    ...
    obj.render(request) --> "<h1>Index</h1>"

By default, all render methods are XML escaped unless decorated with
L{@xml<xml>}.  By using C{@xml}, the implementor is taking responsibility
for ensuring the result is properly escaped and safe from injection
attacks.

Template strings are resources stored alongside python module code, in a
file ending in C{.strings}::

    example.py        # Contains class ExampleRenderObject
    example.strings   # Contains string ExampleRenderObject.greeting

The C{.strings} file can contain multiple templates, each one marked by a
heading in square brackets::

    [ExampleRenderObject.greeting]
    Hello, {user_name}

    [SomeOtherRenderObject.valediction]
    Goodbye, {user_name}

The key inside the brackets is composed of a class name and a template
name, separated by a dot.  The render object looks up strings by an
object's immediate class, and then, in method resolution order, each
ancestor class.

By default, every render object starts with a single main template.  You
can call out to another template by name::

    [ExampleRenderObject.main]
    <div class="greeting">{greeting_template}</div>

Additional templates are added by creating child objects on the render
object::

    class ExampleRenderObject(RenderObject):
        def __init__(self):
            super().__init__()

            self.greeting_template = Template(self, "greeting")
"""

from .common import *

import functools as _functools
import inspect as _inspect
import types as _types

_log = logger("disco.render")

def xml(meth):
    """
    A decorator to disable the standard XML escaping of a render method

    If a render method is decorated with C{@xml}, the implementor must
    ensure the rendered result is properly escaped for inclusion in an
    HTML document.

    @see: L{xml_escape}
    @see: L{url_escape}

    @type meth: callable
    @param meth: The method to decorate

    @rtype: callable
    @return: The decorated method
    """

    meth._xml = True
    return meth

def _render_xml(func):
    @_functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if result is None:
            return ""

        return result

    return wrapper

def _render_escaped(func):
    @_functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)

        if result is None:
            return ""

        return xml_escape(result)

    return wrapper

class RenderObject:
    """
    An object with its render methods coupled to one or more
    L{RenderTemplates<RenderTemplate>}

    @type templates: iterable<L{RenderTemplate}>
    @ivar templates: A list of object templates in creation order

    @type templates_by_name: dict<basestring, L{RenderTemplate}>
    @ivar templates_by_name: A dictionary of object templates by template
    name

    @type main_template: L{RenderTemplate}
    @ivar main_template: The template used by default in L{render}

    @group Setup: __init__, init, add_render_method, bind_templates
    @group Response generation: render*

    @undocumented: __repr__
    """

    def __init__(self):
        """
        Create a render object
        """

        self.templates = list()
        self.templates_by_name = dict()

        self.main_template = RenderTemplate(self, "main")

        classes = [x.__name__ for x in self.__class__.__mro__]
        classes = classes[:-1]

        self._classes = " ".join(classes)

    def _get_string(self, name):
        for cls in self.__class__.__mro__:
            if cls is object:
                msg = "String for name '{}' not found for class '{}'"
                raise Exception(msg.format(name, self.__class__.__name__))

            module = sys.modules[cls.__module__]

            try:
                strings = module.__dict__["_strings"]
            except KeyError:
                continue

            qualified_name = "{}.{}".format(cls.__name__, name)

            try:
                return strings[qualified_name]
            except KeyError:
                pass

    def init(self):
        """
        Initialize the object
        """

        _log.debug("Initializing %s", self)

        for template in self.templates:
            template._init()

    def add_render_method(self, name, func):
        """
        Add a named render method to this object

        Typically one would just define a render method directly on the
        class.  This alternative allows you to define methods
        programatically.

        Methods must be added before calling L{bind_templates}.

        @type name: basestring
        @param name: The method name; it must start with C{render_}

        @type func: callable
        @param func: The method implementation
        """

        assert not hasattr(self, name)
        assert name.startswith("render_")
        assert callable(func)

        meth = _types.MethodType(func, self)
        setattr(self, name, meth)

    def bind_templates(self):
        """
        Bind the templates to the object

        This method must be called by subclasses at the end of
        initialization.
        """

        _log.debug("Binding templates of %s", self)

        for name, meth in _inspect.getmembers(self, _inspect.ismethod):
            if not name.startswith("render"):
                continue

            if hasattr(meth, "_xml"):
                meth = _render_xml(meth)
            else:
                meth = _render_escaped(meth)
                
            setattr(self, name, meth)

        for template in self.templates:
            template._bind()

    @xml
    def render(self, request):
        """
        Render the object using L{main_template}

        @type request: L{PageRequest}
        @param request: The request for the current request

        @rtype: basestring
        @return: The rendered result
        """

        _log.debug("Rendering %s", self)

        return self.main_template.render(request)

    def render_classes(self, request):
        """
        Render class names for use in CSS selectors

        The class names include the immediate class and all ancestor
        classes up to and including L{RenderObject}::

            <div class="{classes}">...</div>
            ...
            <div class="ExampleRenderObject RenderObject">...</div>

        @type request: L{PageRequest}
        @param request: The request for the current request

        @rtype: basestring
        @return: A space-separated list of class names
        """

        return self._classes

    def __repr__(self):
        return fmt_repr(self)

class RenderTemplate:
    """
    A template string with placeholders bound to L{RenderObject} C{render}
    methods

    @type object: L{RenderObject}
    @ivar object: The object the template is bound to

    @type name: basestring
    @ivar name: The template name

    @group Setup: __init__, delete
    @group Response generation: render

    @undocumented: __repr__
    """

    def __init__(self, _object, name):
        """
        Create a template
        """

        assert isinstance(_object, RenderObject)

        self._object = _object
        self._name = name

        self._elements = None

        assert self.name not in self.object.templates_by_name

        self.object.templates.append(self)
        self.object.templates_by_name[self.name] = self

    @property
    def object(self):
        return self._object

    @property
    def name(self):
        return self._name

    def delete(self):
        """
        Delete the template
        """

        self.object.templates.remove(self)
        del self.object.templates_by_name[self.name]

    def _init(self):
        meth_name = "render_{}_template".format(self.name)

        def meth(obj, request):
            return self.render(request)

        self.object.add_render_method(meth_name, xml(meth))

    def _bind(self):
        assert self._elements is None

        string = self.object._get_string(self.name)
        self._elements = self._parse(string)

    def _parse(self, string):
        elems = list()
        tokens = re.split("({.+?})", string)

        for token in tokens:
            if token.startswith("{") and token.endswith("}"):
                meth_name = "render_{}".format(token[1:-1])
                meth = getattr(self.object, meth_name, None)

                if meth:
                    elems.append(meth)
                    continue

            elems.append(token)

        return elems

    def render(self, request):
        """
        Render the template

        @type request: L{PageRequest}
        @param request: The request for the current request

        @rtype: basestring
        @return: The rendered result
        """

        out = list()

        for elem in self._elements:
            if callable(elem):
                elem = elem(request)

            out.append(elem)

        return "".join(out)

    def __repr__(self):
        return fmt_repr(self, self.name)
