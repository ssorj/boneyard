export PYTHONPATH := ${CURDIR}/python

.PHONY: run
run: clean
	python3 -m epithet config input output
	@echo file:${CURDIR}/output

.PHONY: clean
clean:
	rm -rf output
	rm -rf python/__pycache__

.PHONY: modules
modules:
	git submodule update --remote
