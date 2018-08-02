DESTDIR := ""
PREFIX := ~/.local
home = ${PREFIX}/share/qpid-management

export PATH := ${PWD}/install/bin:${PATH}
export PYTHONPATH := $(shell scripts/python-path ${PREFIX})

.PHONY: default
default: devel

.PHONY: help
help:
	@echo "build          Build the code"
	@echo "install        Install the code"
	@echo "clean          Clean up the source tree"
	@echo "devel          Build, install, and run a basic test in this checkout"

.PHONY: build
build:
	scripts/configure-files -a qpid_management_home=${home} bin/*.in build/bin

.PHONY: install
install: build
	scripts/install-files build/bin ${DESTDIR}${PREFIX}/bin
	scripts/install-files --name \*.py python ${DESTDIR}${home}/python

.PHONY: devel
devel: PREFIX := ${PWD}/install
devel: install

clean:
	rm -rf build
	rm -rf install
	find python -type f -name \*.pyc -delete
