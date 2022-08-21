.PHONY: default
default:
	@echo "Targets: build, run, test, clean, readme"

.PHONY: build
build:
	cd frontend && mvn package
	cd processor && mvn package

.PHONY: run
run: build
	scripts/run

.PHONY: test
test: build
	scripts/test

.PHONY: clean
clean:
	rm -rf frontend/target
	rm -rf processor/target
	rm -f README.html

.PHONY: readme
readme: README.html

README.html: README.md
	pandoc -o $@ $<
