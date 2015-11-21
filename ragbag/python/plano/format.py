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
import pprint as _pprint
import time as _time

from datetime import datetime as _datetime

_date_format = "%Y-%m-%d %H:%M:%S"

def fmt_local_unixtime(utime=None):
    if utime is None:
        return

    return _time.strftime(_date_format + " %Z", time.localtime(utime))

def fmt_local_unixtime_medium(utime):
    if utime is None:
        return

    return _time.strftime("%d %b %H:%M", time.localtime(utime))

def fmt_local_unixtime_brief(utime):
    if utime is None:
        return

    now = _time.time()

    if utime > now - 86400:
        fmt = "%H:%M"
    else:
        fmt = "%d %b"

    return _time.strftime(fmt, _time.localtime(utime))

def fmt_datetime(dtime):
    if dtime is None:
        return

    return dtime.strftime(_date_format)

def fmt_list(coll):
    if not coll:
        return

    return ", ".join([_pprint.pformat(x) for x in coll])

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
        value = _pprint.pformat(coll[key])
        value = value.replace("\n", "\n%s" % indent)
        args = key, value

        out.append(fmt % args)

    return _os.linesep.join(out)
