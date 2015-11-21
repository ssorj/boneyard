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

_log = logging.getLogger("qpid.peer.delivery")

class Delivery(IdObject):
    def __init__(self, home, node, pn_object):
        super(Delivery, self).__init__()

        self._home = home
        self._node = node
        self._pn_object = pn_object

    def acknowledge(self, disposition=None):
        _log.info("Acknowledging %s with %s", self, disposition)

        if disposition is None:
            disposition = ACCEPTED

        with self._home._lock:
            pn_disp = _pn_dispositions[disposition]
            pn_disposition(message._pn_delivery, pn_disp)
            pn_advance(node._link._pn_object)

        if self._home.sync_acknowledge:
            self.wait_settle()

    def wait_acknowledge(self, disposition=None, timeout=None):
        _log.info("Waiting for acknowledgment of %s", self)

        with self._home._lock:
            def predicate():
                disp = pn_remote_disp(self._pn_object)
                print "XXX", disp
                return disp in (PN_ACCEPTED, PN_REJECTED)

            self._home._wait_cond(predicate, timeout)

            pn_disp = pn_remote_disp(self._pn_object)
            disp = _dispositions[pn_disp]

            if disposition is not None and disposition is not disp:
                raise ProcessingException()

            return disp

    def settle(self):
        _log.info("Settling %s", self)
        
        with self._home._lock:
            pn_settle(self._pn_object)

    def wait_settle(self):
        _log.info("Waiting for settlement of %s", self)

        # XXX How can this be done?

class Disposition(object):
    pass

ACCEPTED = Disposition()
REJECTED = Disposition()
RELEASED = Disposition()

_pn_dispositions = {
    ACCEPTED: PN_ACCEPTED,
    REJECTED: PN_REJECTED,
    RELEASED: PN_RELEASED,
}

_dispositions = {
    PN_ACCEPTED: ACCEPTED,
    PN_REJECTED: REJECTED,
    PN_RELEASED: RELEASED,
}
