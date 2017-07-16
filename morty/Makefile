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

DESTDIR := ""
PREFIX := /usr/local
MORTY_HOME = ${PREFIX}/lib/morty

export PATH := ${PWD}/install/bin:${PATH}

.PHONY: default
default: devel

.PHONY: clean
clean:
	rm -rf build
	rm -rf install

.PHONY: build
build: build/bin/morty

.PHONY: install
install: build
	scripts/install-files lib ${DESTDIR}${MORTY_HOME}/lib
	scripts/install-files node_modules ${DESTDIR}${MORTY_HOME}/node_modules
	scripts/install-files build/bin ${DESTDIR}${PREFIX}/bin

.PHONY: devel
devel: PREFIX := ${PWD}/install
devel: install
	morty "//127.0.0.1/morty"

.PHONY: update-modules
update-modules:
	rm -rf node_modules
	npm install

build/bin/%: bin/%.in
	scripts/configure-file -a morty_home=${MORTY_HOME} $< $@
