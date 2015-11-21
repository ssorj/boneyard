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

_log = logging.getLogger("qpid.peer.driver")

class _Driver(IdObject):
    def __init__(self, home):
        super(_Driver, self).__init__()

        self.home = home

        self.pn_driver = pn_driver()

        if "QPID_PEER_DEBUG" in os.environ:
            pn_driver_trace(self.pn_driver, PN_TRACE_FRM)

    def tick(self):
        self.wait()
        self.process()

    def wait(self):
        #traceback.print_stack()

        _log.debug("Waiting")

        pn_driver_wait(self.pn_driver, 1000)

    def process(self):
        _log.debug("Processing")

        while True:
            listener = pn_driver_listener(self.pn_driver)

            if listener is None:
                break

            connector = pn_listener_accept(listener)

            pn_connector_set_context(connector, None) # XXX
        
        while True:
            connector = pn_driver_connector(self.pn_driver)

            if connector is None:
                break

            pn_connector_process(connector)

            # XXX I don't yet see why the following shouldn't
            # typically be done in the driver c code

            conn = pn_connector_connection(connector)

            if pn_connector_closed(connector):
                pn_connector_destroy(connector)
                continue

            self.process_sasl(connector)

            if pn_connection_state(conn) & PN_LOCAL_UNINIT:
                pn_connection_open(conn)

            self.process_opening_sessions(conn)
            self.process_opening_links(conn)

            self.process_deliveries(conn)

            self.process_closing_links(conn)
            self.process_closing_sessions(conn)

            if pn_connection_state(conn) == PN_LOCAL_ACTIVE | PN_REMOTE_CLOSED:
                pn_connection_close(conn)

    def process_sasl(self, connector):
        sasl = pn_connector_sasl(connector)

        while True:
            state = pn_sasl_state(sasl)

            if state == PN_SASL_PASS:
                return

            if state == PN_SASL_CONF:
                pn_sasl_mechanisms(sasl, "ANONYMOUS")
                pn_sasl_server(sasl)
                continue

            if state == PN_SASL_STEP:
                mech = pn_sasl_remote_mechanisms(sasl)

                if mech == "ANONYMOUS":
                    pn_sasl_done(sasl, PN_SASL_OK)
                    pn_connector_set_connection(connector, pn_connection())
                else:
                    pn_sasl_done(sasl, PN_SASL_AUTH)
                    continue

            if state == PN_SASL_IDLE:
                return # XXX

            if state == PN_SASL_FAIL:
                return

    def process_opening_sessions(self, conn):
        sess = pn_session_head(conn, PN_LOCAL_UNINIT)

        while sess is not None:
            _log.debug("Processing opening session")
            
            pn_session_open(sess)

            sess = pn_session_next(sess, PN_LOCAL_UNINIT)

    def process_closing_sessions(self, conn):
        sess = pn_session_head(conn, PN_LOCAL_ACTIVE | PN_REMOTE_CLOSED)

        while sess is not None:
            _log.debug("Processing closing session")
            
            pn_session_close(sess)

            sess = pn_session_next(sess, PN_LOCAL_ACTIVE | PN_REMOTE_CLOSED)

    def process_opening_links(self, conn):
        link = pn_link_head(conn, PN_LOCAL_UNINIT)

        while link is not None:
            _log.debug("Processing opening link")

            target = pn_remote_target(link)
            source = pn_remote_source(link)

            pn_set_target(link, target)
            pn_set_source(link, source)

            pn_link_open(link)

            if pn_is_receiver(link):
                pn_flow(link, 100) # XXX

            link = pn_link_next(link, PN_LOCAL_UNINIT)

    def process_closing_links(self, conn):
        link = pn_link_head(conn, PN_LOCAL_ACTIVE | PN_REMOTE_CLOSED)

        while link is not None:
            _log.debug("Processing closing link")
            
            pn_link_close(link)

            link = pn_link_next(sess, PN_LOCAL_ACTIVE | PN_REMOTE_CLOSED)

    def process_deliveries(self, conn):
        delivery = pn_work_head(conn)

        while delivery is not None:
            if pn_readable(delivery):
                self.process_read(delivery)

            if pn_writable(delivery):
                self.process_write(delivery)

            if pn_updated(delivery):
                self.process_update(delivery)

            delivery = pn_work_next(delivery)

    def process_read(self, delivery):
        _log.debug("Processing read")

        link = pn_link(delivery)
        tag = pn_delivery_tag(delivery)

        while True:
            code, data = pn_recv(link, 1024)

            if code == PN_EOS:
                break

            if code < 0:
                _log.error("Error %i receiving message", code)
                break

            if data:
                _log.info("Received Message[%s]", tag)

        if pn_credit(link) < 100: # XXX
            pn_flow(link, 100)

    def process_write(self, delivery):
        _log.debug("Processing write")

        link = pn_link(delivery)
        tag = pn_delivery_tag(delivery)

        content = "Message[%s]" % tag
        code, data = pn_message_data(content, 1024)

        if code < 0:
            _log.error("Error %i creating message data", code)
            return

        code = pn_send(link, data)

        if code != len(data):
            _log.error("Error %i sending message", code)
            return

        if not pn_advance(link):
            _log.error("Who knows")
            return

        _log.info("Sent Message[%s]", tag)

    def process_update(self, delivery):
        _log.debug("Processing update")

        if self.home.auto_settle:
            pn_settle(delivery)
