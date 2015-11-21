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
from endpoint import _Receiver
from message import *

_log = logging.getLogger("qpid.peer.source")

class Source(IdObject):
    def __init__(self, home, address, connector):
        super(Source, self).__init__()

        _log.info("Creating %s", self)

        self.home = home
        self.address = address
        self.connector = connector

        assert self.address not in self.home._sources_by_address

        self.home._sources.append(self)
        self.home._sources_by_address[self.address] = self

        session = self.connector._session

        self._receiver = _Receiver(self.home, session, self.address)

    def _get_deliveries(self):
        raise Unimplemented()

    deliveries = property(_get_deliveries)

    def receive(self, message=None, timeout=None):
        _log.info("Receiving from %s", self)

        pn_link = self._receiver.pn_object

        with self.home._lock:
            self._receiver.open()

            pn_flow(link, 1)

            def predicate():
                return pn_current(pn_link) is not None

            self.home._wait_cond(predicate, timeout)

            pn_deliv = pn_current(pn_link)

            tag = pn_delivery_tag(delivery)

            if message is None:
                message = Message()

            message.content = tag

            deliv = Delivery(self.home, self, pn_deliv)
            deliv.message = message

        if self.home.auto_acknowledge:
            deliv.acknowledge(timeout)

        return deliv
