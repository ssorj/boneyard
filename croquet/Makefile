.PHONY: default help prepare build install clean devel

BUILD_DIR := build
DESTDIR := ""
PREFIX := /usr/local

default: help

help:
	@echo "build          Build the code"
	@echo "install        Install the code"
	@echo "clean          Clean up the source tree"

prepare:
	mkdir -p ${BUILD_DIR}/bin
	mkdir -p ${BUILD_DIR}/lib/croquet

build: prepare build/lib/croquet/croquet-receive-qma-cpp
	scripts/configure-file bin/croquet.in "${BUILD_DIR}/bin/croquet" \
		"${PREFIX}/lib/croquet"
	scripts/configure-file bin/croquet-send-qma-python.in \
		"${BUILD_DIR}/lib/croquet/croquet-send-qma-python" \
		"${PREFIX}/lib/croquet"
	scripts/configure-file bin/croquet-receive-qma-python.in \
		"${BUILD_DIR}/lib/croquet/croquet-receive-qma-python" \
		"${PREFIX}/lib/croquet"

install: build
	scripts/install-python-code python \
		"${DESTDIR}${PREFIX}/lib/croquet/python"

	install -d "${DESTDIR}${PREFIX}/bin"
	install -m 755 "${BUILD_DIR}/bin/croquet" "${DESTDIR}${PREFIX}/bin/croquet"
	install -m 755 "${BUILD_DIR}/lib/croquet/croquet-send-qma-python" \
		"${DESTDIR}${PREFIX}/lib/croquet/croquet-send-qma-python"
	install -m 755 "${BUILD_DIR}/lib/croquet/croquet-receive-qma-python" \
		"${DESTDIR}${PREFIX}/lib/croquet/croquet-receive-qma-python"
	install -m 755 "${BUILD_DIR}/lib/croquet/croquet-receive-qma-cpp" \
		"${DESTDIR}${PREFIX}/lib/croquet/croquet-receive-qma-cpp"

clean:
	find python -type f -name \*.pyc -delete
	rm -rf build
	rm -rf install

devel: PREFIX := ${INSTALL_DIR}
devel: clean install

build/lib/croquet/%: cpp/%.cpp
	gcc -std=c++11 -lqpidmessaging -lqpidtypes -lstdc++ $< -o $@
