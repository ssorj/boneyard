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
Classes to describe HTTP clients
"""

from application import *

_log = logger("cabinet.client")

_http_date_gmt = "%a, %d %b %Y %H:%M:%S GMT"

class ClientSession(AttributeObject):
    """
    Attributes describing a connected HTTP client

     - It is created once when a client first visits
     - It is expired after one hour without activity
     - It is attached to the HTTP client via a session cookie
     - It holds the user's login account
     - It takes arbitrary application variables as attributes

    Operations on the client session must be made thread-safe by using
    L{lock}::

        client = page.get_client_session(session)

        with client.lock:
            x = client.x
            client.x = x + 1

    Single gets or sets are safe without locking.

    @type app: L{Application}
    @ivar app: The application to which this client session belongs

    @type lock: Lock
    @ivar lock: A lock for use when performing any compound operation

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

    @undocumented: __init__, __repr__
    """

    def __init__(self, app):
        super(ClientSession, self).__init__()

        self._app = app
        self._id = unique_id()

        _log.debug("Creating %s", self)

        self._lock = Lock()

        self.created = datetime.now()
        self.touched = self.created

        self.account = None
        self.form_nonce = None
        self.result_message = None

        self.app._client_sessions_by_id[self._id] = self

    @property
    def app(self):
        return self._app

    @property
    def lock(self):
        return self._lock

    def _delete(self):
        with self._lock:
            del self.app._client_sessions_by_id[self._id]

    def _touch(self):
        self.touched = datetime.now()

    def _copy_with_new_id(self):
        with self.lock:
            other = ClientSession(self.app)
            other._attributes_by_name.update(self._attributes_by_name)
            return other

    def get_and_set(self, name, value):
        """
        Atomically get and set an attribute

        @type name: basestring
        @param name: The attribute name

        @type value: object
        @param value: The new attribute value

        @rtype: object
        @return: The old attribute value
        """

        with self.lock:
            prev = getattr(self, name)
            setattr(self, name, value)
            return prev

    def __repr__(self):
        args = self.__class__.__name__, self._id[:4]
        return "%s(%s)" % args

class _ClientSessionExpireThread(ApplicationThread):
    def __init__(self, app):
        super(_ClientSessionExpireThread, self).__init__(app, "expire")

    def do_run(self):
        while True:
            self.expire_sessions()
            time.sleep(60)

    def expire_sessions(self):
        when = datetime.now() - timedelta(hours=1)
        count = 0

        for client in self.app._client_sessions_by_id.values():
            if client.touched < when:
                client._delete()
                count += 1

        _log.debug("Expired %i client %s", count, plural("session", count))
