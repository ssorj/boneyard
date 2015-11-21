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

from home import *

_log = logging.getLogger("qpid.peer.test")

def test_hello(interface, port):
    home = Home(interface, port)
    home.send(Message("Howdy"))

def test_client(interface, port):
    #import pdb; pdb.set_trace()

    home = Home(interface, port)

    queue1 = home.create_target("queue1")
    queue2 = home.create_target("queue2")

    msg1 = Message("alpha")
    msg2 = Message("beta")

    home.default_connector.connect()

    while True:
        queue1.send(msg1)
        queue2.send(msg2)
        
        home.wait()

def test_server(interface, port):
    #import pdb; pdb.set_trace()

    home = Home(interface, port)
    home.default_listener.start()
    home.run()

if __name__ == "__main__":
    os.environ['QPID_PEER_DEBUG'] = "Hello, Bugs"

    add_logging("qpid.peer", "debug", sys.stdout)

    name, interface, port = sys.argv[1:4]

    tests = globals()

    test = tests["test_%s" % name]

    try:
        test(interface, port)
    except:
        _log.exception("Unexpected error")
