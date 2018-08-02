#!/usr/bin/env bash
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

set -e

if [[ -z "$SOURCE_DIR" ]]; then
    echo "Run 'source config.sh' first"
    exit 1
fi

install.sh

qmtest --help > /dev/null
qmlist --help > /dev/null
qmquery --help > /dev/null
qmcall --help > /dev/null

port=$(python -c "import random; print random.randint(49152, 65535)")
$INSTALL_DIR/share/qpid-management/bin/test-server $port &
test_server_pid=$!

#python -c "import socket; sock = socket.socket(); sock.connect((\"localhost\", $port))"
sleep 0.2

qmtest --disable-dynamic-response-node --port $port

qmlist types --port $port --disable-dynamic-response-node
qmlist attributes --port $port --disable-dynamic-response-node
qmlist operations --port $port --disable-dynamic-response-node
qmlist other-nodes --port $port --disable-dynamic-response-node

kill $test_server_pid
wait $test_server_pid
