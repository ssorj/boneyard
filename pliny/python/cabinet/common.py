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
Common utility classes and functions

@group Content escaping: url_escape, url_unescape, xml_escape, xml_unescape
@group HTML utility functions: strip_tags, encode_href

@undocumented: __package__
"""

import os
import random
import re
import sys
import time
import traceback
import types

from collections import deque, defaultdict
from datetime import datetime, timedelta
from pprint import pprint, pformat
from threading import Lock

from polly.string import *
from polly.util import *
from polly.logging import *

# URL and XML escaping, other markup functions

from urllib import urlencode as encode_qs

from urllib import quote_plus as _url_escape
from urllib import unquote_plus as _url_unescape

from xml.sax.saxutils import escape as _xml_escape
from xml.sax.saxutils import unescape as _xml_unescape

def url_escape(string):
    if string is None: return
    return _url_escape(string)

def url_unescape(string):
    if string is None:
        return

    return _url_unescape(string)

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

_strip_tags_regex = re.compile(r"<[^<]+?>")

def strip_tags(string):
    if string is None:
        return

    return re.sub(_strip_tags_regex, "", string)

# Result is not xml escaped
def encode_href(path, **parameters):
    if not parameters:
        return path

    for name, value in parameters.items():
        if name.startswith("_"):
            del parameters[name]
            parameters[name[1:]] = value

    args = path, encode_qs(parameters)
    return "%s?%s" % args

# Miscellaneous

class AttributeObject(object):
    """
    A class for attributes    
    """

    def __init__(self):
        """
        Create an attribute object
        """

        self._attributes_by_name = dict()

    def __hasattr__(self, name):
        """
        Check if an attribute is set
        """

        return name in self._attributes_by_name

    def __getattr__(self, name, default=None):
        """
        Get an attribute value
        """

        return self._attributes_by_name[name]

    def __setattr__(self, name, value):
        """
        Set an attribute value
        """

        if name.startswith("_"):
            return super(AttributeObject, self).__setattr__(name, value)

        self._attributes_by_name[name] = value

    def __delattr__(self, name):
        """
        Delete an attribute
        """

        if name.startswith("_"):
            return super(AttributeObject, self).__delattr__(name, value)

        del self._attributes_by_name[name]

class StringCatalog(dict):
    def __init__(self, path):
        super(StringCatalog, self).__init__()

        self.path = "%s.strings" % os.path.splitext(path)[0]

        self.load()

    def load(self):
        with open(self.path) as file:
            strings = self._parse(file)

        self.update(strings)

    def _parse(self, file):
        strings = dict()
        key = None
        out = list()

        for line in file:
            line = line.rstrip()

            if line.startswith("[") and line.endswith("]"):
                if key:
                    strings[key] = "".join(out).strip()

                out = list()
                key = line[1:-1]

                continue

            out.append(line)
            out.append("\r\n")

        strings[key] = "".join(out).strip()

        return strings

    def __repr__(self):
        args = self.__class__.__name__, self.path
        return "%s(%s)" % args

from html import *
from render import *
