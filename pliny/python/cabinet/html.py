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
Functions for generating HTML

 - Keyword arguments are converted to element attributes
 - Any leading underscores on keywords are stripped, so you can work around certain Python reserved words
 - Attribute values are XML escaped
 - Element content is I{not} escaped

@group Basic: html_open, html_close, html_elem
@group General: html_link, html_div, html_span, html_li, html_p
@group Tables: html_tr, html_th, html_td
@group Forms: html_input, html_checkbox_input, html_radio_input, html_option, html_button
@group Extensions: html_none, html_property_list
"""

from common import *

_log = logger("cabinet.html")

def _html_elem(tag, content, attrs):
    attrs = _html_attrs(attrs)

    if content is None:
        args = tag, attrs
        return "<%s%s/>" % args

    args = tag, attrs, content, tag
    return "<%s%s>%s</%s>" % args

def _html_attrs(attrs):
    if "_class" in attrs:
        attrs["class"] = attrs.pop("_class")

    attrs = [" %s=\"%s\"" % (k, xml_escape(v)) for (k, v) in attrs.items()]
    return "".join(attrs)

def html_open(tag, **attributes):
    """<tag attribute="value">"""
    args = tag, _html_attrs(attributes)
    return "<%s%s>" % args

def html_close(tag):
    """</tag>"""
    return "</%s>" % tag

def html_elem(tag, content, **attributes):
    """<tag attribute="value">content</tag>"""
    return _html_elem(tag, content, attributes)

def html_p(content, **attributes):
    return _html_elem("p", content, attributes)

def html_tr(content, **attributes):
    return _html_elem("tr", content, attributes)

def html_th(content, **attributes):
    return _html_elem("th", content, attributes)

def html_td(content, **attributes):
    return _html_elem("td", content, attributes)

def html_li(content, **attributes):
    return _html_elem("li", content, attributes)

def html_link(content, href, **attributes):
    attributes["href"] = href
    return _html_elem("a", content, attributes)

def html_div(content, **attributes):
    return _html_elem("div", content, attributes)

def html_span(content, **attributes):
    return _html_elem("span", content, attributes)

def html_option(content, value, selected=False, **attributes):
    attributes["value"] = value

    if selected:
        attributes["selected"] = "selected"

    return _html_elem("option", content, attributes)

def html_input(name, value=None, type="text", **attributes):
    attributes["name"] = name
    attributes["type"] = type

    if value is not None:
        attributes["value"] = value

    return _html_elem("input", None, attributes)

def html_checkbox_input(name, value, checked=False, **attributes):
    if checked:
        attributes["checked"] = "checked"

    return html_input(name, value, "checkbox", **attributes)

def html_radio_input(name, value, checked=False, **attributes):
    if checked:
        attributes["checked"] = "checked"

    return html_input(name, value, "radio", **attributes)

def html_button(content, name, value=None, type="submit", **attributes):
    attributes["name"] = name
    attributes["type"] = type

    if value is not None:
        attributes["value"] = value

    return _html_elem("button", content, attributes)

# Extensions

def html_none():
    """
    Generate an element with class "none" and containing the text "None".
    """
    return "<div class=\"none\">None</div>"

def html_property_list(properties):
    """
    Generate a table of property names and values.

    @type properties: iterable<tuple>
    @param properties: The name-value pairs to display
    """
    out = list()
    out.append(html_open("table", _class="property-list"))

    for name, value in properties:
        if value is None:
            value = html_none()

        args = html_th(name), html_td(str(value))
        out.append(html_tr("".join(args)))

    out.append(html_close("table"))

    return "".join(out)
