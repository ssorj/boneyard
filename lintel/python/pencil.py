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

import re as _re

# String formatting functions

def shorten(s, max):
    if len(s) < max:
        return s
    else:
        return s[0:max]

def nvl(value, substitution, template=None):
    if value is None:
        return substitution

    if template is not None:
        return template.format(value)

    return value

def init_cap(s):
    return s[0].upper() + s[1:]

def first_sentence(text):
    if not text:
        return ""

    match = _re.search(r"(.+?)\.\s+", text, _re.DOTALL)

    if match is None:
        if text.endswith("."):
            text = text[:-1]
        
        return text
    
    return match.group(1)

# HTML functions

from xml.sax.saxutils import escape as _xml_escape
from xml.sax.saxutils import unescape as _xml_unescape

_extra_entities = {
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;",
}

def xml_escape(string):
    if string is None:
        return

    return _xml_escape(string, _extra_entities)

def xml_unescape(string):
    if string is None:
        return

    return _xml_unescape(string)

def _html_elem(tag, content, attrs):
    attrs = _html_attrs(attrs)

    if content is None:
        content = ""
    
    return "<{}{}>{}</{}>".format(tag, attrs, content, tag)

def _html_attrs(attrs):
    vars = list()

    for name, value in attrs.items():
        if value is False:
            continue

        if value is True:
            value = name
            
        if name == "class_" or name == "_class":
            name = "class"

        vars.append(" {}=\"{}\"".format(name, xml_escape(value)))

    return "".join(vars)

def html_open(tag, **attrs):
    """<tag attribute="value">"""
    args = tag, _html_attrs(attrs)
    return "<{}{}>".format(tag, _html_attrs(attrs))

def html_close(tag):
    """</tag>"""
    return "</{}>".format(tag)

def html_elem(tag, content, **attrs):
    """<tag attribute="value">content</tag>"""
    return _html_elem(tag, content, attrs)

def html_p(content, **attrs):
    return _html_elem("p", content, attrs)

def html_tr(content, **attrs):
    return _html_elem("tr", content, attrs)

def html_th(content, **attrs):
    return _html_elem("th", content, attrs)

def html_td(content, **attrs):
    return _html_elem("td", content, attrs)

def html_li(content, **attrs):
    return _html_elem("li", content, attrs)

def html_a(content, href, **attrs):
    attrs["href"] = href

    return _html_elem("a", content, attrs)

def nvl_html_a(value, substitution, href_template):
    if value is None:
        return substitution

    return html_a(value, href_template.format(value))

def html_h(content, **attrs):
    return _html_elem("h1", content, attrs)

def html_div(content, **attrs):
    return _html_elem("div", content, attrs)

def html_span(content, **attrs):
    return _html_elem("span", content, attrs)

def html_section(content, **attrs):
    return _html_elem("section", content, attrs)

def html_table(items, first_row_headings=True, first_col_headings=False,
               **attrs):
    row_headings = list()
    rows = list()

    if first_row_headings:
        for cell in items[0]:
            row_headings.append(html_th(cell))

        rows.append(html_tr("".join(row_headings)))

        items = items[1:]
        
    for item in items:
        cols = list()

        for i, cell in enumerate(item):
            if i == 0 and first_col_headings:
                cols.append(html_th(cell))
            else:
                cols.append(html_td(cell))

        rows.append(html_tr("".join(cols)))

    tbody = html_elem("tbody", "\n{}\n".format("\n".join(rows)))
        
    return _html_elem("table", tbody, attrs)

def html_ul(items, **attrs):
    out = list()
    
    for item in items:
        out.append(html_li(item))

    return _html_elem("ul", "".join(out), attrs)
