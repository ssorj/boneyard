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

from collections import defaultdict as _defaultdict
import logging as _logging
import sys as _sys
import threading as _threading
import os as _os

_logging_modules = list()

_logging_levels_by_name = {
    "debug": _logging.DEBUG,
    "info": _logging.INFO,
    "warn": _logging.WARN,
    "error": _logging.ERROR,
    "critical": _logging.CRITICAL
    }

_logging_handlers_by_logger = _defaultdict(list)

class _StreamHandler(_logging.StreamHandler):
    def __repr__(self):
        args = self.__class__.__name__, self.level, self.stream.name
        return "%s(%s,%s)" % args

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

def print_logging(name):
    log = _logging.getLogger(name)
    handlers = _logging_handlers_by_logger[log]

    for handler in handlers:
        print handler

def setup_initial_logging():
    # XXX maybe
    _threading.current_thread().name = "main"

    log_level = "warn"

    if "PLINY_DEBUG" in _os.environ:
        log_level = "debug"

    for name in _logging_modules:
        add_logging(name, log_level, _sys.stderr)

def setup_console_logging(level):
    for name in _logging_modules:
        clear_logging(name)

    for name in _logging_modules:
        add_logging(name, level, _sys.stderr)

def setup_server_logging(level, file):
    for name in _logging_modules:
        clear_logging(name)

    if "PLINY_DEBUG" in _os.environ:
        for name in _logging_modules:
            add_logging(name, "debug", _sys.stderr)

    if file is not None:
        for name in _logging_modules:
            add_logging(name, level, file)

logger = _logging.getLogger

def add_logging_module(name):
    _logging_modules.append(name)
