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
from driver import _Driver
from endpoint import _Connection, _Session

_log = logging.getLogger("qbit.peer.connector")

class Connector(IdObject):
    def __init__(self, home):
        super(Connector, self).__init__()

        self.home = home

    def connect(self, timeout=None):
        with self.home._lock:
            self.do_connect(timeout)

    def do_connect(self, timeout=None):
        raise Unimplemented()

    def disconnect(self, timeout=None):
        with self.home._lock:
            self.do_disconnect(timeout)

    def do_disconnect(self, timeout=None):
        raise Unimplemented()
    
    # Caller must hold lock
    def _process(self):
        raise Unimplemented()

class TcpConnector(Connector):
    def __init__(self, home, interface="localhost.localdomain", port="5672"):
        super(TcpConnector, self).__init__(home)

        self.interface = interface
        self.port = port

        self.username = None
        self.password = None

        self._connection = _Connection(self.home)
        self._session = _Session(self.home, self._connection)

        self._pn_connector = None

    def do_connect(self, timeout=None):
        if self._pn_connector is not None:
            if pn_connector_closed(self._pn_connector):
                pn_connector_destroy(self._pn_connector)
                self._pn_connector = None
            else:
                return

        _log.info("Opening %s", self)

        driver = self.home._driver.pn_driver
        self._pn_connector = pn_connector \
            (driver, self.interface, self.port, self)

        pn_connector_set_connection \
            (self._pn_connector, self._connection.pn_object)

        self._authenticate()

        self._connection.open()
        self._session.open()

    def _authenticate(self, timeout=None):
        _log.info("Authenticating %s", self)

        sasl = pn_connector_sasl(self._pn_connector)

        if self.username is None:
            pn_sasl_mechanisms(sasl, "ANONYMOUS")
            pn_sasl_client(sasl)
        else:
            pn_sasl_plain(sasl, self.username, self.password)

        def predicate():
            return pn_sasl_outcome(sasl) == PN_SASL_OK

        self.home._wait_cond(predicate, timeout)

    def _close(self):
        _log.info("Closing %s", self)

        self._session.close()
        self._connection.close()

        pn_connector_close(self._pn_connector)
        pn_connector_destroy(self._pn_connector)
        self._pn_connector = None

    def _process(self):
        if self._pn_connector is not None:
            pn_connector_process(self._pn_connector)
