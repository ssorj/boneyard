.PHONY: default build install clean-checkouts clean-cycles clean-sources \
	clean-installs clean-instance check

PTOLEMY_HOME := $(shell mktemp -d)
PROJECTS := \
	${PTOLEMY_HOME}/projects/qpid \
	${PTOLEMY_HOME}/projects/cumin

default:
	@echo "Hi!"

build:
	python -c "import compileall, re; compileall.compile_dir('python', rx=re.compile('/\.svn'), force=True)"

install: build ${PROJECTS}
	install -d ${PTOLEMY_HOME}/bin
	install -d ${PTOLEMY_HOME}/branches
	install -d ${PTOLEMY_HOME}/config
	install -d ${PTOLEMY_HOME}/cycles
	install -d ${PTOLEMY_HOME}/lib
	install -d ${PTOLEMY_HOME}/log
	install -d ${PTOLEMY_HOME}/projects
	install -pm 0644 etc/ptolemy.config ${PTOLEMY_HOME}/config
	install -pm 0755 bin/ptolemy-* bin/ptol ${PTOLEMY_HOME}/bin
	bin/install-recursively bash \*.bash ${PTOLEMY_HOME}/lib
	bin/install-recursively python \*.py ${PTOLEMY_HOME}/lib
	bin/install-recursively python \*.pyc ${PTOLEMY_HOME}/lib

${PTOLEMY_HOME}/projects/%: projects/%
	install -d $@
	install -pm 0755 $</project.bash $@
	install -pm 0644 $</project.config $@
	install -pm 0755 $</*.script $@

clean-checkouts:
	for proj in projects/*; do rm -rf "$${proj}/checkout"; done

clean-instance: clean-cycles clean-branches
	rm -f instance/log/*.log

clean-cycles:
	rm -rf instance/cycles/*

clean-branches:
	rm -rf instance/branches/*

clean:
	find python -name \*.pyc -delete

tags:
	find python -name \*.py -print | etags -

check:
	mkdir ${PTOLEMY_HOME}/log
	ptolemy-harness --help
	ptolemy-harness --init-only something
	ptolemy-alert-server --help
	ptolemy-alert-server --init-only
	ptolemy-harness-server --help
	ptolemy-harness-server --init-only
	ptolemy-model-server --help
	ptolemy-model-server --init-only
