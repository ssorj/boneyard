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

class HtmlRenderer(PumpjackRenderer):
    def __init__(self, output_dir):
        super(HtmlRenderer, self).__init__(output_dir)

    def include_file(self, path):
        #return "" # XXX

        path = os.path.join(self.output_dir, path)

        if not os.path.exists(path):
            return ""

        with open(path, "r") as file:
            out = file.read()

        if out is None:
            return ""

        return out

    def render_model(self, out, model):
        for module in model.modules:
            self.render_module(out, module)

    def render_module(self, out, module):
        args = initcap(module.model.name), initcap(module.name)
        title = "%s %s" % args

        out.write(html_section_open(title, "module"))
        out.write(html_text(module.doc))
        out.write(self.include_file("module.html"))

        if module.classes:
            out.write(html_section_open("Classes"))
            
            for cls in module.classes:
                self.render_class(out, cls)

            out.write(html_section_close())

        if module.exceptions:
            out.write(html_section_open("Exceptions"))
            
            for exc in module.exceptions:
                self.render_exception(out, exc)

            out.write(html_section_close())

        out.write(html_section_close())

    def render_class(self, out, cls):
        args = cls.doc_id, cls.name
        title = "%s. %s" % args
        
        out.write(html_section_open(title, "class", toggle_visibility=True))
        out.write(html_text(cls.doc))
        out.write(self.include_file("%s.class.html" % cls.name))

        if cls.attributes:
            out.write(html_section_open("Attributes", "attributes"))

            for attr in cls.attributes:
                self.render_attribute(out, attr)

            out.write(html_section_close())

        methods = [x for x in cls.methods if not x.private]

        if methods:
            out.write(html_section_open("Methods", "methods"))

            for meth in methods:
                self.render_method(out, meth)

            out.write(html_section_close())

        out.write(html_section_close())

    def render_exception(self, out, exc):
        args = exc.doc_id, exc.name
        title = "%s. %s" % args

        out.write(html_section_open(title, "exception", toggle_visibility=True))
        out.write(html_text(exc.doc))
        out.write(self.include_file("%s.exception.html" % exc.name))
        out.write(html_section_close())

    def render_attribute(self, out, attr):
        value = ""

        if attr.value is not None:
            value = fmt_node_value(attr)
            value = "= %s" % value
            value = html_span(value, "signature")

        args = attr.name, value
        title = "%s %s" % args

        out.write(html_section_open(title, "attribute", toggle_visibility=True))

        out.write(html_table_open("props"))
        out.write(html_prop_table_entry("Type", attr.type))
        out.write(html_prop_table_entry("Initial value", attr.value))
        out.write(html_prop_table_entry("Nullable?", str(attr.nullable)))
        out.write(html_table_close())

        out.write(html_text(attr.doc))
        out.write(self.include_file("%s.attribute.html" % attr.name))
        out.write(html_section_close())

    def render_method(self, out, meth):
        signature = ", ".join([x.name for x in meth.inputs])
        signature = "(%s)" % signature

        if meth.outputs:
            output = meth.outputs[0]
            args = signature, fmt_node_value(output)
            signature = "%s = %s" % args

        signature = html_span(signature, "signature")

        args = meth.name, signature
        title = "%s %s" % args

        out.write(html_section_open(title, "method", toggle_visibility=True))

        self.render_method_params(out, meth)

        out.write(html_text(meth.doc))
        out.write(self.include_file("%s.method.html" % meth.name))
        out.write(html_section_close())

    def render_method_params(self, out, meth):
        out.write(html_table_open("params"))

        for input in meth.inputs:
            args = input.name, input.type, str(input.nullable)
            out.write("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % args)

        out.write(html_table_close())

    def render_toc(self, out, nodes):
        if not nodes:
            return

        out.write("<table class=\"toc\"><tbody>")

        for node in nodes:
            args = node.name, first_sentence(node.doc)
            out.write("<tr><th>%s</th><td>%s</td></tr>" % args)
        
        out.write("</tbody></table>")

    def render_properties(self, out, node, names):
        out.write("<table class=\"props\"><tbody>")

        for name in names:
            args = initcap(name), node.attrib[name]
            out.write("<tr><th>%s</th><td>%s</td></tr>" % args)
        
        out.write("</tbody></table>")

add_renderer("html", HtmlRenderer)

def html_heading(text, attrs=()):
    attrs_string = " ".join(attrs)
    args = attrs_string, text, attrs_string
    return "<h1 %s>%s</h1 %s>" % args

def html_link(text, href=None, attrs=None):
    if attrs is None:
        attrs = list()

    if href is not None:
        attrs.append("href=\"%s\"" % href)

    args = " ".join(attrs), text
    return "<a %s>%s</a>" % args

def html_para(text):
    return "<p>%s</p>" % text

def html_text(text):
    if not text:
        return ""

    text = re.sub("{", "<a href=\"\">", text) # XXX
    text = re.sub("}", "</a>", text)

    text = re.sub("\s*\n\s*\n\s*", " </p>\n\n<p>", text)

    return "<p>%s</p>" % text

def html_span(text, html_class):
    args = html_class, text
    return "<span class=\"%s\">%s</span>" % args

section_sequence = 0

def html_section_open(heading_text=None,
                      html_class=None,
                      toggle_visibility=False):
    global section_sequence
    section_sequence += 1

    lines = list()

    if heading_text:
        if toggle_visibility:
            link_attrs = list()
            link_attrs.append("class=\"visibility-toggle\"")
            link_attrs.append("target-id=\"%i\"" % section_sequence)

            args = heading_text, html_link("&#187", attrs=link_attrs)
            heading_text = "%s %s" % args

        lines.append(html_heading(heading_text))

    attrs = list()

    attrs.append("id=\"%s\"" % section_sequence)

    if html_class:
        attrs.append("class=\"%s\"" % html_class)

    lines.append("<section %s>" % " ".join(attrs))

    return "\n".join(lines)

def html_section_close():
    return "</section>"

def html_table_open(html_class):
    return "<table class=\"%s\"><tbody>" % html_class

def html_prop_table_entry(name, value):
    args = name, value
    return "<tr><th>%s</th><td>%s</td></tr>" % args

def html_table_close():
    return "</tbody></table>"

def fmt_node_value(node):
    value = node.value

    if node.type == "string":
        value = "'%s'" % value
    elif node.type[0] == "@":
        value = "%s instance" % node.type[1:]

    return value
