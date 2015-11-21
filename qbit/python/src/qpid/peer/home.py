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
from connector import *
from driver import _Driver
from listener import *
from message import *
from source import *
from target import *

_log = logging.getLogger("qpid.peer.home")

class Home(IdObject):
    def __init__(self, address="localhost.localdomain", port="5672"):
        super(Home, self).__init__()

        self._lock = Lock()
        self._driver = _Driver(self)
        self._delivery_sequence = -1

        self._sources = list()
        self._sources_by_address = dict()

        self._targets = list()
        self._targets_by_address = dict()

        self.default_connector = TcpConnector(self, address, port)
        self.default_listener = TcpListener(self, address, port)
        self.default_timeout = 60

        self.sync_send = True
        self.sync_acknowledge = True

        self.auto_connect = True
        self.auto_acknowledge = False
        self.auto_settle = True

    def wait(self):
        with self._lock:
            self._driver.tick()

    def next_event(self):
        raise Unimplemented()

    def run(self):
        while True:
            self.wait()

    # Caller must hold lock
    def _wait_cond(self, predicate, timeout=None):
        if timeout is None:
            timeout = self.default_timeout

        deadline = time.time() + timeout

        while not predicate():
            self._driver.tick()

            if time.time() > deadline:
                raise Timeout()

    def create_source(self, address, connector=None):
        if connector is None:
            connector = self.default_connector

        with self._lock:
            return Source(self, address, connector)

    def create_target(self, address, connector=None):
        if connector is None:
            connector = self.default_connector

        with self._lock:
            return Target(self, address, connector)

    def receive(self, message=None, address=None, timeout=None):
        with self._lock:
            try:
                source = self._sources_by_address[address]
            except KeyError:
                source = Source(self, address, self.default_connector)

        source.connector.connect() # Idempotent

        return source.receive(message, timeout)

    def send(self, message, address=None, timeout=None):
        assert message is not None

        if address is None:
            address = message.address

        with self._lock:
            try:
                target = self._targets_by_address[address]
            except KeyError:
                target = Target(self, address, self.default_connector)

        target.connector.connect() # Idempotent

        return target.send(message, timeout)

    def __enter__(self):
        self.default_connector.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_value is not None:
            _log.exception("Unexpected error")

        self.default_connector.disconnect()
