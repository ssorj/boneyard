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

import os as _os
import sys as _sys
import pprint as _pprint

import logging as _logging
import time as _time

from datetime import datetime as _datetime
from threading import enumerate as _enumerate_threads
from uuid import uuid4 as _uuid4

_log = _logging.getLogger("polly.util")

# Time

def unixtime_to_datetime(utime):
    return _datetime.fromtimestamp(utime)

def datetime_to_unixtime(dtime):
    return _time.mktime(dtime.timetuple()) + 1e-6 * dtime.microsecond

# Collections

def sorted_by(seq, attr="name"):
    return sorted_by_attr(seq, attr)

def sorted_by_attr(seq, attr):
    return sorted(seq, cmp, lambda x: getattr(x, attr))

def sorted_by_index(seq, index):
    return sorted(seq, cmp, lambda x: x[index])

# Other

def print_threads(writer=_sys.stdout):
    row = "%-20.20s  %-20.20s  %-12.12s  %-8s  %-8s  %s"

    writer.write("-" * 78)
    writer.write(_os.linesep)
    writer.write(row % ("Class", "Name", "Ident", "Alive", "Daemon", ""))
    writer.write(_os.linesep)
    writer.write("-" * 78)
    writer.write(_os.linesep)

    for thread in sorted(_enumerate_threads()):
        cls = thread.__class__.__name__
        name = thread.name
        ident = thread.ident
        alive = thread.is_alive()
        daemon = thread.daemon

        writer.write(row % (cls, name, ident, alive, daemon, ""))
        writer.write(_os.linesep)

def nvl(expr1, expr2):
    if expr1 is None:
        return expr2

    return expr1

def unique_id():
    return str(_uuid4())
