.PHONY: build install clean

include ../etc/Makefile.common

name := parsley
lib := ${PYTHON_LIB_DIR}/${name}

build:
	python -m compileall -x '/\.svn' -f python

install: build
	install -d ${lib}
	install python/parsley/*.py python/parsley/*.pyc ${lib}

clean: clean-python-files
