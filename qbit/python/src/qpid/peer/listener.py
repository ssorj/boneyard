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

_log = logging.getLogger("qpid.peer.listener")

class Listener(IdObject):
    def __init__(self, home):
        super(Listener, self).__init__()

        self.home = home

    def start(self):
        _log.info("Starting %s", self)

        with self.home._lock:
            self.do_start()

    def do_start(self):
        raise Unimplemented()

    def stop(self):
        _log.info("Stopping %s", self)

        with self.home._lock:
            self.do_stop()

    def do_stop(self):
        raise Unimplemented()
        
class TcpListener(Listener):
    def __init__(self, home, interface="localhost.localdomain", port="5672"):
        super(TcpListener, self).__init__(home)

        self.interface = interface
        self.port = port

        # User database fields here

        self._pn_listener = None

    def do_start(self):
        driver = self.home._driver.pn_driver
        self._pn_listener = pn_listener(driver, self.interface, self.port, self)

    def do_stop(self):
        pass # XXX
