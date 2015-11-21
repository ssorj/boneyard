.PHONY: default build install clean-checkouts clean-cycles clean-sources \
clean-installs clean-instance

PREFIX := /usr/local
PYTHON_LIB_DIR := ${PREFIX}/lib/python
BIN_DIR := ${PREFIX}/bin
ETC_DIR := ${PREFIX}/etc
VAR_DIR := ${PREFIX}/var

RPM_OUTPUT_DIR := rpms

name := ptolemy

lib := ${PYTHON_LIB_DIR}/${name}
etc := ${ETC_DIR}/${name}
data := ${VAR_DIR}/lib/${name}
log := ${VAR_DIR}/log/${name}

default:
	@echo "Hi!"

build:
	python -c "import compileall, re; compileall.compile_dir('python', rx=re.compile('/\.svn'), force=True)"

install: \
	${data}/projects/qpid \
	${data}/projects/qpid-specs \
	${data}/projects/qpid-cpp \
	${data}/projects/qpid-cpp-distcheck \
	${data}/projects/qpid-cpp-test \
	${data}/projects/qpid-cpp-store \
	${data}/projects/qpid-dotnet \
	${data}/projects/qpid-java \
	${data}/projects/qpid-java-cpp \
	${data}/projects/qpid-java-cpp-ssl \
	${data}/projects/qpid-java-cpp-noprefetch \
	${data}/projects/qpid-java-cpp-cluster \
	${data}/projects/qpid-java-cpp-store \
	${data}/projects/qpid-python \
	${data}/projects/qpid-ruby \
	${data}/projects/qpid-jms-tck \
	${data}/projects/qpid-stable \
	${data}/projects/qpid-stable-specs \
	${data}/projects/qpid-stable-cpp \
	${data}/projects/qpid-stable-cpp-test \
	${data}/projects/qpid-stable-cpp-store \
	${data}/projects/qpid-stable-java \
	${data}/projects/qpid-stable-java-test \
	${data}/projects/qpid-stable-python \
	${data}/projects/qpid-stable-ruby \
	${data}/projects/qpid-stable-jms-tck \
	${data}/projects/cumin \
	build
	install -d ${BIN_DIR}
	install -pm 0755 bin/ptolemy* bin/ptol ${BIN_DIR}
	install -d ${data}/projects/common
	install -pm 0644 projects/common/*.bash ${data}/projects/common
	install -pm 0755 projects/common/*.script ${data}/projects/common
	install -d ${lib}
	ln -s ${lib} ${data}/lib
	install -pm 0644 python/ptolemy/*.py python/ptolemy/*.pyc ${lib}
	install -d ${lib}/server
	install -pm 0644 python/ptolemy/server/*.py python/ptolemy/server/*.pyc ${lib}/server
	install -d ${log}
	ln -s ${log} ${data}/log
	install -d ${etc}
	ln -s ${etc} ${data}/etc
	install -pm 0644 etc/server.conf ${etc}

${data}/projects/%: projects/%
	install -d $@
	install -pm 0644 $</project.conf $@
	install -pm 0755 $</*.script $@

${data}/projects/qpid-jms-tck: projects/qpid-jms-tck
	install -d $@
	install -pm 0644 $</project.conf $@
	install -pm 0755 $</*.script $@
	install -pm 0644 $</log4j.properties $@
	install -pm 0644 $</ts.jte $@
	install -pm 0644 $</jndi.properties.in $@

${data}/projects/qpid-stable-jms-tck: projects/qpid-stable-jms-tck
	install -d $@
	install -pm 0644 $</project.conf $@
	install -pm 0755 $</*.script $@
	install -pm 0644 $</log4j.properties $@
	install -pm 0644 $</ts.jte $@
	install -pm 0644 $</jndi.properties.in $@

clean-checkouts:
	for proj in projects/*; do rm -rf "$${proj}/checkout"; done

clean-instance: clean-cycles clean-sources clean-installs
	rm -f instance/log/server.log

clean-cycles:
	rm -rf instance/cycles

clean-sources:
	rm -rf instance/sources

clean-installs:
	rm -rf instance/installs

tags:
	find python -name \*.py -print | etags --output="etc/devel.tags" -
