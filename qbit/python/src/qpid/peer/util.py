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

import logging
import os
import sys
import time
import traceback

from threading import Thread, Condition, Lock 
from Queue import Queue, Empty
from collections import deque, defaultdict

_logging_modules = ("qpid",)

_logging_levels_by_name = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARN,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
    }

_logging_handlers_by_logger = defaultdict(list)

class _StreamHandler(logging.StreamHandler):
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

    fmt = "# %(msecs)-3d  %(threadName)-12s  %(levelname)-6s  %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    handler.setLevel(level)

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)

    _logging_handlers_by_logger[log].append(handler)

def clear_logging(name):
    log = logging.getLogger(name)

    handlers = _logging_handlers_by_logger[log]

    for handler in handlers:
        log.removeHandler(handler)

    del _logging_handlers_by_logger[log]

def print_logging(name):
    log = logging.getLogger(name)

    handlers = _logging_handlers_by_logger[log]

    for handler in handlers:
        print handler

class Unimplemented(Exception):
    pass

class Timeout(Exception):
    pass

class IdObject(object):
    _sequence = -1
    _sequence_lock = Lock()

    def __init__(self):
        self.id = self.__class__._get_next_id()

    @classmethod
    def _get_next_id(cls):
        with cls._sequence_lock:
            cls._sequence += 1
            return cls._sequence

    def __repr__(self):
        args = self.__class__.__name__, self.id
        return "%s(%i)" % args
