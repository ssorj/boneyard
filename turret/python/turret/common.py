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

from __future__ import absolute_import

"""
Common utility classes and functions

@group Content escaping: url_escape, url_unescape, xml_escape, xml_unescape
@group HTML utility functions: strip_tags, encode_href

@undocumented: __package__
"""

import os
import re
import sys
import time

from collections import deque, defaultdict
from datetime import datetime, timedelta
from pprint import pprint, pformat

import logging as _logging
import threading as _threading
import uuid as _uuid

# Logging

_logging_modules = list()

_logging_levels_by_name = {
    "debug": _logging.DEBUG,
    "info": _logging.INFO,
    "warn": _logging.WARN,
    "error": _logging.ERROR,
    "critical": _logging.CRITICAL
    }

_logging_handlers_by_logger = defaultdict(list)

class _StreamHandler(_logging.StreamHandler):
    def __repr__(self):
        return fmt_repr(self, self.level, self.stream.name)

def add_logging(name, level, file):
    assert level, level
    assert file, file

    if isinstance(level, str):
        level = _logging_levels_by_name[level.lower()]

    if isinstance(file, str):
        file = open(file, "a")
 
    handler = _StreamHandler(file)

    fmt = "%(threadName)-6.6s %(asctime)s %(levelname)-4.4s %(message)s"
    handler.setFormatter(_logging.Formatter(fmt))
    handler.setLevel(level)

    log = _logging.getLogger(name)
    log.setLevel(_logging.DEBUG)
    log.addHandler(handler)

    _logging_handlers_by_logger[log].append(handler)

def clear_logging(name):
    log = _logging.getLogger(name)
    handlers = _logging_handlers_by_logger[log]

    for handler in handlers:
        log.removeHandler(handler)

    del _logging_handlers_by_logger[log]

def setup_initial_logging():
    _threading.current_thread().name = "main"

    log_level = "warn"

    if "TURRET_DEBUG" in os.environ:
        log_level = "debug"

    for name in _logging_modules:
        add_logging(name, log_level, sys.stderr)

def setup_console_logging(level):
    for name in _logging_modules:
        clear_logging(name)

    if "TURRET_DEBUG" in os.environ:
        level = "debug"

    for name in _logging_modules:
        add_logging(name, level, sys.stderr)

def setup_server_logging(level, file):
    for name in _logging_modules:
        clear_logging(name)

    if "TURRET_DEBUG" in os.environ:
        for name in _logging_modules:
            add_logging(name, "debug", sys.stderr)

    if file is not None:
        for name in _logging_modules:
            add_logging(name, level, file)

logger = _logging.getLogger

def add_logging_module(name):
    _logging_modules.append(name)

add_logging_module("turret")

# URL and XML escaping, other markup functions

from urllib.parse import urlencode as encode_qs

from urllib.parse import quote_plus as _url_escape
from urllib.parse import unquote_plus as _url_unescape

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

    return "{}?{}".format(path, encode_qs(parameters))

# Miscellaneous

def plural(noun, count=0):
    if noun is None:
        return

    if count == 1:
        return noun

    if noun.endswith("s"):
        return "{}ses".format(noun)

    return "{}s".format(noun)

def fmt_list(coll):
    if not coll:
        return

    return ", ".join([pformat(x) for x in coll])

def fmt_dict(coll):
    if not coll:
        return

    if not isinstance(coll, dict) and hasattr(coll, "__iter__"):
        coll = dict(coll)

    out = list()
    key_len = max([len(str(x)) for x in coll])
    key_len = min(48, key_len)
    key_len += 2
    indent = " " * (key_len + 2)
    fmt = "%%-%ir  %%s" % key_len

    for key in sorted(coll):
        value = pformat(coll[key])
        value = value.replace("\n", "\n{}".format(indent))
        args = key, value

        out.append(fmt % args)

    return os.linesep.join(out)

def fmt_repr(obj, *args):
    cls = obj.__class__.__name__
    strings = [str(x) for x in args]
    return "{}({})".format(cls, ",".join(strings))

def _print_threads(writer=sys.stdout):
    #row = "%-20.20s  %-20.20s  %-12.12s  %-8s  %-8s  %s"
    row = "{:-20.20}  {:-20.20}  {:-12.12}  {:-8}  {:-8}  {}"
    
    writer.write("-" * 78)
    writer.write(os.linesep)
    writer.write(row.format("Class", "Name", "Ident", "Alive", "Daemon", ""))
    writer.write(os.linesep)
    writer.write("-" * 78)
    writer.write(os.linesep)

    for thread in sorted(_threading.enumerate()):
        cls = thread.__class__.__name__
        name = thread.name
        ident = thread.ident
        alive = thread.is_alive()
        daemon = thread.daemon

        writer.write(row.format(cls, name, ident, alive, daemon, ""))
        writer.write(os.linesep)

def unique_id():
    return str(_uuid.uuid4())

class AttributeDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
