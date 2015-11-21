#!/usr/bin/python
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


from xml.etree.ElementTree import *
from util import *

class _Node(object):
    def __init__(self, element, parent):
        self.element = element
        self.name = element.attrib.get("name")
        self.group = self.element.attrib.get("group")
        self.private = self.element.attrib.get("private", False)

        #args = self.__class__.__name__, self.name
        #print "Creating %s(%s)" % args

        self.doc = element.text

        if self.doc:
            self.doc = self.doc.strip()

        self.parent = parent
        self.children = list()
        self.children_by_name = dict()

        if self.parent:
            if self.name in self.parent.children_by_name:
                raise Exception("Collision! %s", self.name)
            
            self.parent.children.append(self)
            self.parent.children_by_name[self.name] = self

        node = self
        self.ancestors = list()

        while node.parent:
            node = node.parent
            self.ancestors.append(node)

        self.model = node

    def process_children(self):
        for child in self.children:
            child.process_children()

    def process_references(self):
        for child in self.children:
            child.process_references()

    def resolve_reference(self, ref):
        if not ref.startswith("@"):
            raise Exception("'%s' doesn't look like a ref", ref)

        if ref.startswith("@/"):
            path = ref[2:].split("/")[1:]

            name = None
            node = self.model

            while path:
                name = path.pop(0)

                try:
                    node = node.children_by_name[name]
                except KeyError:
                    msg = "Cannot find child '%s' on node '%s'"
                    raise Exception(msg, name, node.name)

            return node
        else:
            node = None

            for ancestor in self.ancestors:
                if isinstance(ancestor, _Module):
                    node = ancestor
                    break

            if node:
                name = ref[1:]

                try:
                    return node.children_by_name[name]
                except KeyError:
                    msg = "Cannot find child '%s' on node '%s'"
                    raise Exception(msg, name, node.name)

class _Module(_Node):
    def __init__(self, element, parent):
        super(_Module, self).__init__(element, parent)

        self.classes = list()
        self.exceptions = list()
        self.enumerations = list()

    def process_children(self):
        for child in self.element.findall("exception"):
            exc = _Exception(child, self)
            self.exceptions.append(exc)

        for child in self.element.findall("class"):
            cls = _Class(child, self)
            self.classes.append(cls)

        for child in self.element.findall("enumeration"):
            enum = _Enumeration(child, self)
            self.enumerations.append(enum)

        super(_Module, self).process_children()

class _Class(_Node):
    def __init__(self, element, parent):
        super(_Class, self).__init__(element, parent)

        self.constructor = None

        self.type = self.element.attrib.get("type")

        self.attributes = list()
        self.attributes_by_group = defaultdict(list)

        self.methods = list()
        self.methods_by_group = defaultdict(list)

        self.constants = list()
        self.constants_by_group = defaultdict(list)

        self.doc_id = "C%i" % (self.parent.children.index(self) - 1)

    def process_children(self):
        for child in self.element.findall("attribute"):
            attr = _Attribute(child, self)
            self.attributes.append(attr)
            self.attributes_by_group[attr.group].append(attr)

        child = self.element.find("constructor")

        if child is not None:
            self.constructor = _Method(child, self)
            self.methods.append(self.constructor)
            self.methods_by_group[self.constructor.group].append \
                (self.constructor)

        for child in self.element.findall("method"):
            meth = _Method(child, self)
            self.methods.append(meth)
            self.methods_by_group[meth.group].append(meth)

        for child in self.element.findall("constant"):
            const = _Constant(child, self)
            self.constants.append(const)
            self.constants_by_group[const.group].append(const)

        super(_Class, self).process_children()

class _Enumeration(_Node):
    def __init__(self, element, parent):
        super(_Enumeration, self).__init__(element, parent)

        self.constants = list()
        self.constants_by_group = defaultdict(list)

    def process_children(self):
        for child in self.element.findall("constant"):
            const = _Constant(child, self)
            self.constants.append(const)
            self.constants_by_group[const.group].append(const)

        super(_Enumeration, self).process_children()

class _Parameter(_Node):
    def __init__(self, element, parent):
        super(_Parameter, self).__init__(element, parent)

        self.type = self.element.attrib.get("type")
        self.value = self.element.attrib.get("value")
        self.nullable = self.element.attrib.get("nullable", False)

class _Constant(_Parameter):
    def __init__(self, element, parent):
        super(_Constant, self).__init__(element, parent)

class _Attribute(_Parameter):
    def __init__(self, element, parent):
        super(_Attribute, self).__init__(element, parent)

        self.writeable = True
        self.readable = True

        writeable = self.element.attrib.get("writeable")
        readable = self.element.attrib.get("readable")

        if writeable == "false":
            self.writeable = False

        if readable == "false":
            self.readable = False

        args = self.parent.doc_id, (self.parent.children.index(self) + 1)
        self.doc_id = "%s.%i" % args

class _Method(_Node):
    def __init__(self, element, parent):
        super(_Method, self).__init__(element, parent)

        self.inputs = list()
        self.outputs = list()
        self.exception_conditions = list()

        args = self.parent.doc_id, self.parent.children.index(self)
        self.doc_id = "%s.%i" % args

    def process_children(self):
        for child in self.element.findall("input"):
            input = _Parameter(child, self)
            self.inputs.append(input)

        for child in self.element.findall("output"):
            output = _Parameter(child, self)
            self.outputs.append(output)

        for child in self.element.findall("exception-condition"):
            cond = _ExceptionCondition(child, self)
            self.exception_conditions.append(cond)

        super(_Method, self).process_children()

class _ExceptionCondition(_Node):
    def __init__(self, element, parent):
        super(_ExceptionCondition, self).__init__(element, parent)
        self.exception_ref = self.element.attrib["exception"]
        self.exception = None

    def process_references(self):
        self.exception = self.resolve_reference(self.exception_ref)

        super(_ExceptionCondition, self).process_references()

class _Exception(_Node):
    def __init__(self, element, parent):
        super(_Exception, self).__init__(element, parent)

        self.doc_id = "E%i" % self.parent.children.index(self)

class _Type(_Node):
    def __init__(self, element, parent):
        super(_Type, self).__init__(element, parent)

class PumpjackModel(_Node):
    def __init__(self, element):
        super(PumpjackModel, self).__init__(element, None)

        self.modules = list()
        self.types = list()

    def process(self):
        self.process_children()
        self.process_references()

    def process_children(self):
        for child in self.element.findall("module"):
            module = _Module(child, self)
            self.modules.append(module)

        for child in self.element.findall("type"):
            type = _Type(child, self)
            self.types.append(type)

        super(PumpjackModel, self).process_children()
