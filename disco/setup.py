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

data_files = [
    ("share/disco/files", [
        "files/disco.js",
        "files/disco.css",
        "files/main.js",
        "files/main.css",
        ]),
    ("share/disco/files/fonts/Roboto-Condensed", [
        "files/fonts/Roboto-Condensed/Roboto-Condensed-Bold-Italic.woff",
        "files/fonts/Roboto-Condensed/Roboto-Condensed-Bold.woff",
        "files/fonts/Roboto-Condensed/Roboto-Condensed-Italic.woff",
        "files/fonts/Roboto-Condensed/Roboto-Condensed-Light-Italic.woff",
        "files/fonts/Roboto-Condensed/Roboto-Condensed-Light.woff",
        "files/fonts/Roboto-Condensed/Roboto-Condensed-Regular.woff",
        ])]

setup(name="disco",
      version="0.1",
      data_files=data_files,
      packages=["disco"],
      package_data={"": ["*.strings"]},
      package_dir={"": "python"},
      scripts=["bin/disco-demo"])
