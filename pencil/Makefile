.PHONY: default help build install clean devel

DESTDIR := ""
PREFIX := /usr/local

default: devel

help:
	@echo "build          Build the code"
	@echo "install        Install the code"
	@echo "clean          Remove transient files from the checkout"
	@echo "devel          Clean, build, install, and test for"
	@echo "               this development session [default]"

build:
	./setup.py build

install: build
	./setup.py install --prefix ${DESTDIR}${PREFIX}

clean:
	find python -type f -name \*.pyc -delete
	./setup.py clean --all
	rm -rf install

devel: PREFIX := install
devel: clean install
	scripts/test-pencil
	./setup.py check
