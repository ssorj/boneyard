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

class CRenderer(PumpjackRenderer):
    prefix = "qp"

    def __init__(self, output_dir):
        super(CRenderer, self).__init__(output_dir)

        self.type_literals["string"] = "const char *"
        self.type_literals["boolean"] = "bool"
        self.type_literals["integer"] = "int"
        self.type_literals["any"] = "void *"
        self.type_literals["class"] = "int"

    def render_class_name(self, cls):
        args = self.prefix, cls.name.replace("-", "_")
        return "%s_%s_t" % args

    def render_method_name(self, meth):
        return meth.name.replace("-", "_")

    def render_var_name(self, var):
        return var.name.replace("-", "_")

    def render_model(self, out, model):
        for type in model.types:
            self.render_type(out, type)

        out.write()

        for module in model.modules:
            self.render_module(out, module)

    def render_module(self, out, module):
        out.write("// module %s.%s", module.parent.name, module.name)
        out.write()
        out.write("#include <stdbool.h>")
        out.write()

        for cls in module.classes:
            name = self.render_class_name(cls)
            out.write("typedef struct %s %s;", name, name)

        out.write()

        for enum in module.enumerations:
            self.render_enumeration(out, enum)
            out.write()

        for cls in module.classes:
            self.render_class(out, cls)
            out.write()

        #out.write()
        #out.write("void main(int argc, char * argv) {}")

        #for exc in module.exceptions:
        #    self.render_exception(out, exc)

    def render_class(self, out, cls):
        #name = self.render_class_name(cls)
        #out.write("typedef struct %s %s;", name, name)
        #out.write()

        out.write("/// %s ///", cls.name)

        if cls.constructor:
            out.write()
            self.render_constructor(out, cls.constructor)
            self.render_destructor(out, cls)

        for attr in cls.attributes:
            out.write()
            self.render_attribute(out, attr)

        for meth in cls.methods:
            out.write()
            self.render_method(out, meth)

    def render_constructor(self, out, ctor):
        return_type = self.render_class_name(ctor.parent)
        cls_name = self.render_var_name(ctor.parent)

        inputs = list()

        for input in ctor.inputs:
            args = (self.get_type_literal(ctor, input.type),
                    self.render_var_name(input))
            inputs.append("%s %s" % args)

        args = ", ".join(inputs)

        out.write("%s * %s_%s(%s);", return_type, self.prefix, cls_name, args)

    def render_destructor(self, out, cls):
        cls_name = self.render_var_name(cls)
        obj_arg = "%s * this" % self.render_class_name(cls)

        out.write("void %s_%s_destroy(%s);", self.prefix, cls_name, obj_arg)

    def render_attribute(self, out, attr):
        cls_name = self.render_var_name(attr.parent)
        attr_name = self.render_var_name(attr)

        obj_arg = "%s * this" % self.render_class_name(attr.parent)

        value_type = self.get_type_literal(attr, attr.type)
        value_arg = "%s value" % value_type

        if attr.writeable:
            args = self.prefix, cls_name, attr_name
            meth_name = "%s_%s_set_%s" % args
            out.write("void %s(%s, %s);", meth_name, obj_arg, value_arg)

        if attr.readable:
            args = self.prefix, cls_name, attr_name

            if attr.type == "boolean":
                meth_name = "%s_%s_is_%s" % args
            else:
                meth_name = "%s_%s_get_%s" % args

            out.write("%s %s(%s);", value_type, meth_name, obj_arg)

    def render_method(self, out, meth):
        cls_name = self.render_var_name(meth.parent)
        obj_arg = "%s * this" % self.render_class_name(meth.parent)

        inputs = list((obj_arg,))

        for input in meth.inputs:
            args = (self.get_type_literal(meth, input.type),
                    self.render_var_name(input))
            inputs.append("%s %s" % args)

        if meth.outputs:
            output = meth.outputs[0]
            return_type = self.get_type_literal(meth, output.type)
        else:
            return_type = "void"

        name = self.render_method_name(meth)
        args = ", ".join(inputs)
        out.write("%s %s_%s_%s(%s);",
                  return_type, self.prefix, cls_name, name, args)

    def render_exception(self, out, exc):
        raise Exception()

    def render_enumeration(self, out, enum):
        name = self.render_class_name(enum)

        out.write("typedef enum %s {", name)

        for const in enum.constants:
            out.write("    %s,", self.render_var_name(const).upper())

        out.write("} %s;", name)

    def render_type(self, out, type):
        literal = self.type_literals[type.name]
        out.write("// type %s -> %s", type.name, literal)

add_renderer("c", CRenderer)

