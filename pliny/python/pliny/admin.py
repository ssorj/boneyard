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

from database import *

_log = logger("pliny.admin")

class PlinyAdmin(object):
    def __init__(self, home, config):
        self.home = home
        self.config = config

        self.debug = "PLINY_DEBUG" in os.environ

        self.database = Database(self, self.config.admin.database_file)

    def init(self):
        _log.info("Initializing %s", self)

        self.database.init()

    def load_demo_data(self):
        session = DatabaseSession()

        try:
            session.add(User(name="aconway", email="aconway@example.com"))
            session.add(User(name="astitcher", email="astitcher@example.com"))
            session.add(User(name="cjansen", email="cjansen@example.com"))
            session.add(User(name="crolke", email="crolke@example.com"))
            session.add(User(name="mcpierce", email="mcpierce@example.com"))
            session.add(User(name="ernie", email="ernie@example.com"))
            session.add(User(name="gsim", email="gsim@example.com"))
            session.add(User(name="irina", email="irina@example.com"))
            session.add(User(name="jross", email="jross@example.com"))
            session.add(User(name="kgiusti", email="kgiusti@example.com"))
            session.add(User(name="kpvdr", email="kpvdr@example.com"))
            session.add(User(name="mcressman", email="mcressman@example.com"))
            session.add(User(name="mick", email="mick@example.com"))
            session.add(User(name="rhs", email="rhs@example.com"))
            session.add(User(name="rajith", email="rajith@example.com"))
            session.add(User(name="tross", email="tross@example.com"))
            session.add(User(name="wprice", email="wprice@example.com"))

            for user in session.query(User):
                for name in "news", "jobs", "build.results", "build.output":
                    name = "%s.%s" % (user.name, name)
                    session.add(Queue(name=name, user=user))

            session.commit()
        finally:
            session.close()

    def __repr__(self):
        args = self.__class__.__name__, self.home
        return "%s(%s)" % args
