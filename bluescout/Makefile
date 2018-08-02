export PATH := ${PWD}/build/bin:${PATH}

.PHONY: build
build:
	npm install -g --prefix ${PWD}/build

.PHONY: test-1
test-1: build
	send amqps://localhost examples abc
	receive amqps://localhost examples 1

.PHONY: test-2
test-2: build
	MESSAGING_SERVICE_URL=amqps://localhost:5672 main

.PHONY: deps
deps:
	npm install

.PHONY: clean
clean:
	rm -rf node_modules
	rm -rf build
