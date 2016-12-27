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

from cabinet.account import *
from data import *
from home import *
from user import *
from queue import *

class PlinyWeb(Application):
    def __init__(self, home, config):
        super(PlinyWeb, self).__init__ \
            (home,
             config.web.host, config.web.port,
             config.web.ssl_cert, config.web.ssl_key)
            
        self.config = config

        self.debug = "PLINY_DEBUG" in os.environ

        self.title = "Pliny"

        self.database = Database(self, self.config.web.database_file)
        self.account_database = AccountDatabase(self)

        self.home_frame = HomeFrame(self, "home")
        self.account_frame = AccountFrame(self, "account")
        self.user_frame = UserFrame(self, "user")
        self.queue_frame = QueueFrame(self, "queue")
        self.file_frame = FileFrame(self, "file")
        self.data_frame = DataFrame(self, "data")

        self.default_frame = self.home_frame
        self.account_frame.database_adapter = self.account_database

    def init(self):
        super(PlinyWeb, self).init()

        self.database.init()

    def receive(self, request):
        session = self.database.get_session()
        request.attributes["database_session"] = session

        try:
            return super(PlinyWeb, self).receive(request)
        finally:
            session.close()

    def process(self, session):
        session.database = session.request.attributes["database_session"]

    def get_queue_uri(self, queue):
        return "/pliny.example.com/%s" % queue.name
