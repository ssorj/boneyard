.PHONY: build install clean

include ../etc/Makefile.common

name := rosemary

lib := ${PYTHON_LIB_DIR}/${name}
doc := ${DOC_DIR}/${name}
share := ${SHARE_DIR}/${name}

build:
	python -m compileall -x '/\.svn' -f python

install: build
	install -d ${lib}
	install python/rosemary/*.py python/rosemary/*.pyc ${lib}
	install -d ${BIN_DIR}
	install bin/* ${BIN_DIR}
	install -d ${doc}
	install LICENSE COPYING ${doc}

clean: clean-python-files
