.PHONY: default
default: build

.PHONY: help
help:
	@echo "build           Build the code"
	@echo "run             Run the services"
	@echo "clean           Removes build and test artifacts"

.PHONY: build
build:
	mvn package

.PHONY: run
run:
	scripts/run

.PHONY: clean
clean:
	mvn clean
	rm -rf README.html scripts/__pycache__

README.html: README.md
	pandoc $< -o $@
