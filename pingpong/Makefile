DESTDIR := ""
PREFIX := /usr/local
home = ${PREFIX}/share/pingpong

export PATH := ${PWD}/build/bin:${PWD}/node_modules/.bin:${PATH}
export NODE_PATH = ${PWD}/node_modules:/usr/lib/node_modules:/usr/local/lib/node_modules

.PHONY: default
default: test

.PHONY: help
help:
	@echo "help"
	@echo "build"
	@echo "test"
	@echo "test-python"
	@echo "test-javascript"

.PHONY: clean
clean:
	rm -rf build

.PHONY: build
build:
	mkdir -p build/bin
	scripts/configure-file bin/pingpong-client.in build/bin/pingpong-client pingpong_home ${home}
	scripts/configure-file bin/pingpong-server.in build/bin/pingpong-server pingpong_home ${home}
	scripts/configure-file bin/pingpong-client-javascript.in build/bin/pingpong-client-javascript pingpong_home ${home}
	scripts/configure-file bin/pingpong-server-javascript.in build/bin/pingpong-server-javascript pingpong_home ${home}
	scripts/configure-file bin/pingpong-client-python.in build/bin/pingpong-client-python pingpong_home ${home}
	scripts/configure-file bin/pingpong-server-python.in build/bin/pingpong-server-python pingpong_home ${home}
	chmod 755 build/bin/*

.PHONY: test
test: build
	scripts/test python
#	scripts/test javascript

.PHONY: update-rhea
update-rhea:
	rm -rf node_modules/rhea
	scripts/git-export "git@github.com:grs/rhea.git" master node_modules/rhea

# browserify -r rhea -o misc/rhea.js
