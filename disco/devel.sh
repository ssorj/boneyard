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

DEVEL_SOURCE_DIR=$PWD
DEVEL_BUILD_DIR=$DEVEL_SOURCE_DIR/build
DEVEL_INSTALL_DIR=$DEVEL_SOURCE_DIR/install

export DEVEL_SOURCE_DIR DEVEL_BUILD_DIR DEVEL_INSTALL_DIR

DISCO_HOME=$DEVEL_INSTALL_DIR/share/disco
DISCO_DEBUG=1

export DISCO_HOME DISCO_DEBUG

PATH=$DEVEL_INSTALL_DIR/bin:$PATH
PYTHONPATH=$(python3 scripts/get-devel-python-path):$PYTHONPATH

export PATH PYTHONPATH
