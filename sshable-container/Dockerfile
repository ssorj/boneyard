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

FROM registry.fedoraproject.org/fedora-minimal:36

# RUN microdnf -y install python3-pip && microdnf clean all
# RUN pip3 install httpx starlette sse_starlette uvicorn
# COPY python /app/python
# COPY static /app/static
# EXPOSE 8080
# WORKDIR /app
# CMD ["python3", "python/main.py"]

RUN microdnf -y install openssh-server && microdnf clean all

RUN ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N "" \
    && ssh-keygen -t dsa -f /etc/ssh/ssh_host_dsa_key -N "" \
    && ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N "" \
    && ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ""

RUN echo root:welcome | chpasswd

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
