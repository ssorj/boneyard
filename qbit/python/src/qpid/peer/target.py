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
from delivery import *
from endpoint import _Sender
from message import *

_log = logging.getLogger("qpid.peer.target")

class Target(IdObject):
    def __init__(self, home, address, connector):
        super(Target, self).__init__()

        _log.info("Creating %s", self)

        self.home = home
        self.address = address
        self.connector = connector

        assert self.address not in self.home._targets_by_address

        self.home._targets.append(self)
        self.home._targets_by_address[self.address] = self

        session = self.connector._session

        self._sender = _Sender(self.home, session, self.address)

    def _get_credit(self):
        raise Unimplemented()

    credit = property(_get_credit)

    def send(self, message, timeout=None):
        _log.info("Sending %s to %s", message, self)

        pn_link_ = self._sender.pn_object

        with self.home._lock:
            self._sender.open()

            self.home._delivery_sequence += 1
            delivery_id = self.home._delivery_sequence
            delivery_tag = "delivery-%i" % delivery_id

            pn_deliv = pn_delivery(pn_link_, delivery_tag)

            # XXX
            self.home._driver.process()

            deliv = Delivery(self.home, self, pn_deliv)

        if self.home.sync_send:
            disp = deliv.wait_acknowledge(timeout)

            if disp is REJECTED:
                raise Exception("XXX delivery is rejected")

        return deliv
