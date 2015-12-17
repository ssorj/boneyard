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
Classes to describe HTTP client sessions
"""

from .application import *

_log = logger("disco.session")

class Session:
    """
    Attributes describing an HTTP client session

     - It is created once when a client first visits
     - It is expired after one hour without activity
     - It is attached to the HTTP client via a session cookie
     - It holds the user's login account
     - It takes arbitrary application variables as attributes

    @type app: L{Application}
    @ivar app: The application to which this client session belongs

    @type created: datetime
    @ivar created: The time of session creation

    @type touched: datetime
    @ivar touched: The last time of any activity

    @type account: L{AccountAdapter}
    @ivar account: The account of the logged in user

    @type form_nonce: basestring
    @ivar form_nonce: A secret used to authenticate form submissions

    @type result_message: basestring
    @ivar result_message: An arbitrary message used to notify the user
    of the result of their actions

    @type attributes: L{AttributeObject}
    @ivar attributes: Arbitrary application variables

    @undocumented: __init__, __repr__
    """

    def __init__(self, app, request):
        super().__init__()

        self._app = app
        self._id = unique_id()
        self._attributes = AttributeDict()

        _log.debug("Creating %s", self)

        self.created = datetime.now()
        self.touched = self.created

        self.account = None
        self.form_nonce = None
        self.result_message = None

        self._set_references(request)

    @property
    def app(self):
        return self._app

    @property
    def attributes(self):
        return self._attributes

    def _set_references(self, request):
        self.app._sessions_by_id[self._id] = self

    def _delete(self):
        del self.app._sessions_by_id[self._id]

    def _touch(self):
        self.touched = datetime.now()

    def reset_id(self, request):
        """
        Reset the client session ID for the client of this request

        This is used to prevent session-fixation attacks.
        """

        self._delete()
        self._id = unique_id()
        self._set_references(request)

    def __repr__(self):
        return fmt_repr(self, self._id[:4])

class _SessionExpireThread(ApplicationThread):
    def __init__(self, app):
        super().__init__(app, "expire")

    def do_run(self):
        while True:
            self.expire_sessions()
            time.sleep(60)

    def expire_sessions(self):
        when = datetime.now() - timedelta(hours=1)
        count = 0

        for session in self.app._sessions_by_id.values():
            if session.touched < when:
                session._delete()
                count += 1

        _log.debug("Expired %i client %s", count, plural("session", count))
