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

from common import *

import json as _json

class DataFrame(Frame):
    def __init__(self, app, name):
        super(DataFrame, self).__init__(app, name)

    def receive(self, request):
        out = list()
        db = request.attributes["database_session"]
        data = self.render_model()

        if len(request.path) >= 2 and request.path[1] == "pretty":
            content = _json.dumps \
                (data, sort_keys=True, indent=4, separators=(",", ": "))
        else:
            content = _json.dumps(data)

        content_type = "application/json"

        return request.respond("200 OK", content, content_type)

    def render_model(self, db):
        users = dict()

        for user in db.query(User).order_by(User.name):
            users[user.name] = self.render_user(user)

        args = {
            "domain": "pliny.example.com",
            "users": users,
        }

        return args

    def render_user(self, user):
        queues = dict()

        for queue in user.queues:
            queues[queue.name] = self.render_queue(queue)

        args = {
            "name": user.name,
            "email": user.email,
            "queues": queues,
        }

        return args

    def render_queue(self, queue):
        args = {
            "name": queue.name,
            "access": queue.access,
            "distribution_mode": queue.distribution_mode,
            "status": queue.status,
            "uri": self.app.get_queue_uri(queue),
        }

        return args
