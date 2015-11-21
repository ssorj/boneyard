#!/usr/bin/env python
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

from distutils.core import setup
from glob import glob

python_files = glob("python/qpid_dispatch_internal/console/*.py") + \
               glob("python/qpid_dispatch_internal/console/*.strings")
web_files = glob("web/*.js") + glob("web/*.css")
font_files = glob("web/fonts/Roboto-Condensed/*")

data_files = [
    ("lib/qpid-dispatch/python/qpid_dispatch_internal",
     ["python/qpid_dispatch_internal/__init__.py"]),
    ("lib/qpid-dispatch/python/qpid_dispatch_internal/console", python_files),
    ("lib/qpid-dispatch/web", web_files),
    ("lib/qpid-dispatch/web/fonts/Roboto-Condensed", font_files),
]

setup(name="rivet",
      version="0.1",
      data_files=data_files,
      scripts=["bin/qdconsoled"])
