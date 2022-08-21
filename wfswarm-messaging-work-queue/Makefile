.PHONY: default
default: build

.PHONY: help
help:
	@echo "build           Build the code"
	@echo "run             Run all the components using a test broker"
	@echo "clean           Removes build and test artifacts"

.PHONY: build
build:
	mvn package

.PHONY: clean
clean:
	mvn clean
	rm -f README.html audit.log

.PHONY: test
test:
	mvn install -Popenshift-it

.PHONY: run
run:
	scripts/run

README.html: README.md
	pandoc $< -o $@
