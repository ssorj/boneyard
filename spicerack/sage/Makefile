.PHONY: build install clean

include ../etc/Makefile.common

name := sage
lib := ${PYTHON_LIB_DIR}/${name}
doc := ${DOC_DIR}/${name}
share := ${SHARE_DIR}/${name}

build:
	python -m compileall -x '/\.svn' -f python

install: build
	install -d ${lib}
	install python/sage/*.py python/sage/*.pyc ${lib}
	install -d ${lib}/aviary
	install python/sage/aviary/*.py python/sage/aviary/*.pyc ${lib}/aviary
	install -d ${lib}/qmf
	install python/sage/qmf/*.py python/sage/qmf/*.pyc ${lib}/qmf
	install -d ${lib}/wallaby
	install python/sage/wallaby/*.py python/sage/wallaby/*.pyc ${lib}/wallaby
	install -d ${share}/rpc-defs/aviary
	install rpc-defs/aviary/* ${share}/rpc-defs/aviary
	install -d ${doc}
	install LICENSE COPYING ${doc}

clean: clean-python-files
