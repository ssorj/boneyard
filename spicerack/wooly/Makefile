.PHONY: build install clean

include ../etc/Makefile.common

name := wooly
lib := ${PYTHON_LIB_DIR}/${name}
doc := ${DOC_DIR}/${name}
share := ${SHARE_DIR}/${name}

build:
	python -m compileall -x '/\.svn' -f python

install: build
	install -d ${lib}
	install -pm 0644 python/wooly/*.py python/wooly/*.pyc python/wooly/*.strings ${lib}
	install -d ${lib}/wsgiserver
	install -pm 0644 python/wooly/wsgiserver/*.py python/wooly/wsgiserver/*.pyc ${lib}/wsgiserver
	install -d ${doc}
	install -pm 0644 LICENSE* COPYING* ${doc}
	install -d ${share}/resources
	install -pm 0644 resources/* ${share}/resources

clean: clean-python-files
