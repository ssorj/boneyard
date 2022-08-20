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

export PYTHONPATH := python:${PYTHONPATH}

DESTDIR := /
PREFIX := ${HOME}/.local

.PHONY: default
default: build

.PHONY: help
help:
	@echo "build          Build the code"
	@echo "test           Run the tests"
	@echo "install        Install the code"
	@echo "clean          Remove transient files from the checkout"

.PHONY: build
build:
	./setup.py build
	./setup.py check

.PHONY: test
test: build
	python2 scripts/test
	python3 scripts/test

.PHONY: install
install: build
	./setup.py install --root ${DESTDIR} --prefix ${PREFIX}

.PHONY: clean
clean:
	find python -type f -name \*.pyc -delete
	rm -rf python/__pycache__ build dist htmlcov .coverage

.PHONY: coverage
coverage:
	coverage run scripts/test
	coverage report
	coverage html
	@echo file:${CURDIR}/htmlcov/index.html
