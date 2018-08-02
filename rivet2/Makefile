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
PREFIX := ${HOME}/.local
RIVET_HOME = ${PREFIX}/share/rivet

export PATH := ${PWD}/install/bin:${PATH}
export PYTHONPATH := ${PWD}/install/share/rivet/python:${PYTHONPATH}

.PHONY: default
default: devel

.PHONY: help
help:
	@echo "build          Build the code"
	@echo "install        Install the code"
	@echo "clean          Remove transient files from the checkout"
	@echo "devel          Clean, build, install, and test inside"
	@echo "               this checkout [default]"

.PHONY: clean
clean:
	find python -type f -name \*.pyc -delete
	rm -rf build
	rm -rf install

.PHONY: build
build:
	scripts/configure-file -a rivet_home=${RIVET_HOME} bin/rivet.in build/bin/rivet

.PHONY: install
install: build
	scripts/install-files -n \*.py python ${DESTDIR}${RIVET_HOME}/python
	scripts/install-files build/bin ${DESTDIR}${PREFIX}/bin

.PHONY: devel
devel: PREFIX := ${PWD}/install
devel: clean install
	rivet test all --release-tag alpha --init-only

.PHONY: test
test: devel
	scripts/test-rivet

.PHONY: update-%
update-%:
	curl "https://raw.githubusercontent.com/ssorj/$*/master/python/$*.py" -o python/$*.py
