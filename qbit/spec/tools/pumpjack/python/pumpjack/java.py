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

from renderer import *

class JavaRenderer(PumpjackRenderer):
    def __init__(self, output_dir):
        super(JavaRenderer, self).__init__(output_dir)

        self.type_literals["string"] = "String"
        self.type_literals["boolean"] = "Boolean"
        self.type_literals["integer"] = "Integer"
        self.type_literals["any"] = "Object"
        self.type_literals["class"] = "Class"

    def render_class_name(self, cls):
        return initcap(studly(cls.name))

    def render_method_name(self, meth):
        return studly(meth.name)

    def render_var_name(self, var):
        return studly(var.name)

    def render_model(self, out, model):
        for type in model.types:
            self.render_type(out, type)

        out.write()

        for module in model.modules:
            self.render_module(out, module)

    def render_module(self, out, module):
        out.write("package %s.%s;", module.parent.name, module.name)
        out.write()

        for cls in module.classes:
            self.render_class(out, cls)
            out.write()

        for exc in module.exceptions:
            self.render_exception(out, exc)
            out.write()

        for enum in module.enumerations:
            self.render_enumeration(out, enum)
            out.write()

        out.write("// End of package %s.%s", module.parent.name, module.name)

        # package_dir = os.path.join \
        #     (self.output_dir, module.parent.name, module.name)

        # makedirs(package_dir)

        # for cls in module.classes:
        #     name = "%s.class" % self.render_class_name(cls)
        #     path = os.path.join(package_dir, name)

        #     file = open(path, "w")
        #     writer = PumpjackWriter(file)

        #     try:
        #         pass # XXXXXXXXXXXXXX
        #     finally:
        #         file.close()

    def render_class(self, out, cls):
        name = self.render_class_name(cls)

        extends_clause = ""

        if cls.type is not None:
            type = self.get_type_literal(cls, cls.type)
            extends_clause = " extends %s" % type

        out.write("interface %s%s {", name, extends_clause)

        if cls.constants:
            for const in cls.constants:
                self.render_constant(out, const)

            out.write()

        if cls.constructor:
            self.render_constructor(out, cls.constructor)
            out.write()

        for attr in cls.attributes:
            self.render_attribute(out, attr)
            out.write()

        for meth in cls.methods:
            self.render_method(out, meth)
            out.write()

        out.write("    // End of class %s", name)
        out.write("}")

    def render_constant(self, out, const):
        name = const.name.upper()
        value = const.value
        out.write("    public static final %s = %s", name, value)

    def render_constructor(self, out, ctor):
        inputs = list()

        for input in ctor.inputs:
            args = self.get_type_literal(ctor, input.type), self.render_var_name(input)
            inputs.append("final %s %s" % args)

        args = ", ".join(inputs)
        out.write("    // %s(%s);", self.render_class_name(ctor.parent), args)

    def render_attribute(self, out, attr):
        value_type = self.get_type_literal(attr, attr.type)

        self.render_doc(out, attr)

        if attr.readable:
            if attr.type == "boolean":
                meth_name = studly("is-%s" % attr.name)
            else:
                meth_name = studly("get-%s" % attr.name)

            out.write("    public %s %s();", value_type, meth_name)

        if attr.writeable:
            meth_name = studly("set-%s" % attr.name)
            out.write("    public void %s(final %s value);",
                      meth_name, value_type)

    def render_method(self, out, meth):
        inputs = list()

        for input in meth.inputs:
            args = self.get_type_literal(meth, input.type), self.render_var_name(input)
            inputs.append("final %s %s" % args)

        self.render_doc(out, meth)
        
        return_type = "void"

        if meth.outputs:
            return_ = meth.outputs[0]
            return_type = self.get_type_literal(meth, return_.type)

        name = self.render_method_name(meth)

        args = ", ".join(inputs)
        out.write("    public %s %s(%s);", return_type, name, args)

        for i in reversed(range(len(meth.inputs))):
            if not meth.inputs[i].nullable:
                break

            args = ", ".join(inputs[0:i])
            out.write("    public %s %s(%s);", return_type, name, args)

    def render_exception(self, out, exc):
        out.write("// class %s extends Exception;", self.render_class_name(exc))

    def render_enumeration(self, out, enum):
        name = self.render_class_name(enum)

        out.write("enum %s {", name)

        for const in enum.constants:
            out.write("    %s,", self.render_var_name(const).upper())

        out.write("}")

    def render_type(self, out, type):
        literal = self.type_literals[type.name]
        out.write("// type %s -> %s", type.name, literal)

    def render_doc(self, out, node):
        out.write("    /**")
        out.write(fmt_comment(node.doc, "     * "))
        out.write("     * ")
        out.write("     * @group %s", node.group)

        if hasattr(node, "inputs"):
            for input in node.inputs:
                input_type = self.get_type_literal(node, input.type)
                input_name = self.render_var_name(input)

                or_null = ""

                if input.nullable:
                    or_null = " or null"

                out.write("     * @param %s %s%s",
                          input_name, input_type, or_null)

        if hasattr(node, "outputs") and node.outputs:
            return_ = node.outputs[0]
            return_type = self.get_type_literal(node, return_.type)
            return_name = self.render_var_name(return_)

            out.write("     * @return %s %s", return_name, return_type)

        out.write("     */")

add_renderer("java", JavaRenderer)
