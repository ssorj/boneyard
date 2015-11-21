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

_log = logging.getLogger("qpid.peer.endpoint")

class _Endpoint(IdObject):
    def __init__(self, home):
        super(_Endpoint, self).__init__()

        self.home = home
        self.pn_object = None

        self.open_state = PN_LOCAL_ACTIVE | PN_REMOTE_ACTIVE
        self.closed_state = PN_LOCAL_CLOSED | PN_REMOTE_CLOSED

    # Caller must hold lock
    def wait_for_state(self, state):
        self.home._driver.process()

        def predicate():
            current_state = self.get_state()

            _log.debug("State -> %s", _get_state_string(current_state))

            return current_state == state

        self.home._wait_cond(predicate)

    # Caller must hold lock
    def get_state(self):
        raise Unimplemented()

    # Caller must hold lock
    def open(self):
        if self.get_state() == self.open_state:
            return

        _log.debug("Opening %s", self)

        assert self.pn_object is not None

        self.do_open()
        self.wait_for_state(self.open_state)

    # Caller must hold lock
    def close(self):
        if self.get_state() == self.closed_state:
            return

        _log.debug("Closing %s", self)

        assert self.pn_object is not None

        self.do_close()
        self.wait_for_state(self.closed_state)

    def do_open(self):
        raise Unimplemented()

    def do_close(self):
        raise Unimplemented()

class _Connection(_Endpoint):
    def __init__(self, home):
        super(_Connection, self).__init__(home)

        self.pn_object = pn_connection()

    def get_state(self):
        return pn_connection_state(self.pn_object)

    def do_open(self):
        pn_connection_open(self.pn_object)

    def do_close(self):
        pn_connection_close(self.pn_object)

class _Session(_Endpoint):
    def __init__(self, home, connection):
        super(_Session, self).__init__(home)

        self.connection = connection
        self.pn_object = pn_session(self.connection.pn_object)

    def get_state(self):
        return pn_session_state(self.pn_object)

    def do_open(self):
        pn_session_open(self.pn_object)

    def do_close(self):
        pn_session_close(self.pn_object)

class _Link(_Endpoint):
    def __init__(self, home, session, address):
        super(_Link, self).__init__(home)

        self.session = session
        self.address = address

    def get_state(self):
        return pn_link_state(self.pn_object)

    def do_open(self):
        pn_link_open(self.pn_object)

    def do_close(self):
        pn_link_close(self.pn_object)

class _Sender(_Link):
    def __init__(self, home, session, address):
        super(_Sender, self).__init__(home, session, address)

        sess = self.session.pn_object
        name = "sender-%i" % self.id

        self.pn_object = pn_sender(sess, name)

        pn_set_target(self.pn_object, self.address)

class _Receiver(_Link):
    def __init__(self, home, session, address):
        super(_Receiver, self).__init__(home, session, address)

        sess = self.session.pn_object
        name = "receiver-%i" % self.id

        self.pn_object = pn_receiver(sess, name)

        pn_set_source(self.pn_object, self.address)

def _check(strings, state, integer, string):
    if state & integer:
        strings.append(string)

def _get_state_string(state):
    strings = list()

    _check(strings, state, PN_LOCAL_UNINIT, "uninit")
    _check(strings, state, PN_LOCAL_ACTIVE, "active")
    _check(strings, state, PN_LOCAL_CLOSED, "closed")

    _check(strings, state, PN_REMOTE_UNINIT, "uninit")
    _check(strings, state, PN_REMOTE_ACTIVE, "active")
    _check(strings, state, PN_REMOTE_CLOSED, "closed")

    return "-".join(strings)
