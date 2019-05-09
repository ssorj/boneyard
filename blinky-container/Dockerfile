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

FROM fedora
MAINTAINER Justin Ross <jross@apache.org>

RUN dnf -qy --setopt deltarpm=0 update && dnf -q clean all

RUN dnf -qy --setopt deltarpm=0 install findutils wget tar make python python3 python3-pyserial python3-requests python3-tornado \
 && dnf -q clean all

WORKDIR /root/blinky

ARG CACHE_BUST=1
RUN wget https://github.com/ssorj/blinky/archive/master.tar.gz \
 && tar -xf master.tar.gz \
 && cd blinky-master \
 && make install PREFIX=/usr

EXPOSE 56720

ADD config.py /etc/blinky/config.py

ENTRYPOINT ["blinky"]
