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

.NOTPARALLEL:

DESTDIR := ""
PREFIX := /usr/local
INSTALLED_ABIGAIL_HOME = ${PREFIX}/lib/abigail

export ABIGAIL_HOME = ${PWD}/build/abigail
export PATH := ${PWD}/build/bin:${PATH}
export PYTHONPATH := ${ABIGAIL_HOME}/python:${PWD}/python:${PYTHONPATH}

VERSION := $(shell cat VERSION.txt)

BIN_SOURCES := $(shell find bin -type f -name \*.in)
BIN_TARGETS := ${BIN_SOURCES:%.in=build/%}

PYTHON_SOURCES := $(shell find python -type f -name \*.py)
PYTHON_TARGETS := ${PYTHON_SOURCES:%=build/abigail/%} ${PYTHON_SOURCES:%.in=build/abigail/%}

.PHONY: default
default: build

.PHONY: help
help:
	@echo "build          Build the code"
	@echo "install        Install the code"
	@echo "clean          Clean up the source tree"
#	@echo "test           Run the tests"

.PHONY: clean
clean:
	find python -type f -name \*.pyc -delete
	find python -type d -name __pycache__ -delete
	rm -rf build

.PHONY: build
build: ${BIN_TARGETS} ${PYTHON_TARGETS} build/prefix.txt

.PHONY: install
install: build
	scripts/install-files build/bin ${DESTDIR}$$(cat build/prefix.txt)/bin
	scripts/install-files build/abigail ${DESTDIR}$$(cat build/prefix.txt)/lib/abigail

build/prefix.txt:
	echo ${PREFIX} > build/prefix.txt

build/bin/%: bin/%.in
	scripts/configure-file -a abigail_home=${INSTALLED_ABIGAIL_HOME} $< $@

build/abigail/python/%: python/%
	@mkdir -p ${@D}
	cp $< $@

.PHONY: update-%
update-%:
	curl "https://raw.githubusercontent.com/ssorj/$*/master/python/$*.py" -o python/$*.py
