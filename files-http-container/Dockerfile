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

RUN dnf -qy --setopt tsflags=nodocs install nginx && dnf -q clean all

COPY nginx.conf /etc/nginx/nginx.conf
COPY web /app/web
ENV HOME=/app

RUN touch /run/nginx.pid

RUN chown -R 1001:0 /app
RUN chown -R 1001:0 /etc/nginx
RUN chown -R 1001:0 /run/nginx.pid && chmod 664 /run/nginx.pid
RUN chown -R 1001:0 /usr/share/nginx
RUN chown -R 1001:0 /var/lib/nginx
RUN chown -R 1001:0 /var/log/nginx && chmod 775 /var/log/nginx

USER 1001
EXPOSE 8080

CMD ["/usr/sbin/nginx"]
