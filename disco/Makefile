.PHONY: default help build install clean devel docs

PREFIX := /usr/local

default: devel

help:
	@echo "install        Install the code"
	@echo "clean          Clean up the source tree"
	@echo "devel          Build and install for this development session"

install:
	python3 setup.py install --prefix ${PREFIX}

clean:
	find python -type f -name \*.pyc -delete
	rm -rf build
	rm -rf install

devel: PREFIX := ${DEVEL_INSTALL_DIR}
devel: clean install
	disco-demo

docs:
	epydoc --no-private disco
