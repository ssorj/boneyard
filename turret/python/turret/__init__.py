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
Overview
========

G{importgraph}

 - Object hierarchy
 - Processing model
 - Forms
 - Accounts

Object hierarchy
================

 - L{Application}
 - L{Frame}
 - L{Page}
 - L{Parameter}

Processing model
================

Request processing
------------------

 - L{ApplicationRequest}
 - C{receive(request)} - L{Application}, L{Frame}, L{Page}
 - L{PageSession}
 - C{process(session)} - L{Application}, L{Frame}, L{Page}
 - check_* methods raise exceptions

Response generation
-------------------

 - C{render(session)} - L{Page.render}, L{FormInput.render}
 - C{render_*} - L{RenderObject}, L{RenderTemplate}

More
====

Setup
-----

 - C{__init__(parent, name)}
 - C{init()}
 - C{delete()}

Page attributes
---------------

 - L{Request}
 - get_title, get_href - app, frame, page
 - get_content_type, add_error, get_errors
 - get_page_navigation_items

Session attributes
-----------------

 - L{Session}
 - session.account
 - session.result_message

@group Model: application, frame, page, parameter
@group Utilities: common, render, html
@group More: session, form, account, debug, wsgi
"""

from .procedure import *
from .file import *
