.phony: build install clean check clean-version write-version mark-local version version-local

include ../etc/Makefile.common

# Attempt to build a version from svn info if we don't already have one
ifndef CUMIN_VERSION
VERSION_REV = $(shell svn info .. 2> /dev/null | fgrep "Last Changed Rev:" | cut -d " " -f 4)
endif

# if CUMIN_VERSION wasn't passed in, and svn info worked, set CUMIN_VERSION
ifneq ($(strip $(VERSION_REV)),)
CUMIN_VERSION =  0.1.$(VERSION_REV)
endif

VERSION_FILE = $(CUMIN_HOME)/version

build:
	python -m compileall -x '/\.svn' -f python

install: CUMIN_HOME := $(shell mktemp -d)
install: build version
	install -d ${CUMIN_HOME}/bin
	install -pm 0755 bin/cumin bin/cumin-* ${CUMIN_HOME}/bin
	install -d ${CUMIN_HOME}/doc
	install -pm 0644 LICENSE COPYING ${CUMIN_HOME}/doc
	install -pm 0644 ../mint/python/mint/plumage/REPORTING-README ${CUMIN_HOME}/doc
	install -pm 0644 ../wooly/LICENSE-for-wsgiserver ${CUMIN_HOME}/doc
	install -pm 0644 ../wooly/COPYING-for-wsgiserver ${CUMIN_HOME}/doc
	install -d ${CUMIN_HOME}/model/upgrades
	install -d ${CUMIN_HOME}/model/access
	install -d ${CUMIN_HOME}/model/plumage
	install -d ${CUMIN_HOME}/model/admin
	install -pm 0644 model/*.xml ${CUMIN_HOME}/model
	- install -pm 0755 model/upgrades/* ${CUMIN_HOME}/model/upgrades/
	install -pm 0644 model/access/*.xml ${CUMIN_HOME}/model/access/
	install -pm 0644 model/plumage/*.xml ${CUMIN_HOME}/model/plumage/
	install -pm 0644 model/admin/*.xml ${CUMIN_HOME}/model/admin/
	install -d ${CUMIN_HOME}/resources
	install -pm 0644 ../wooly/resources/*.css ${CUMIN_HOME}/resources
	install -pm 0644 ../wooly/resources/*.js ${CUMIN_HOME}/resources
	install -pm 0644 ../wooly/resources/plugins/* ${CUMIN_HOME}/resources
	install -pm 0644 resources/* ${CUMIN_HOME}/resources
	install -d ${CUMIN_HOME}/etc
	install -pm 0644 etc/cumin.* ${CUMIN_HOME}/etc
	install -pm 0755 etc/sysvinit-cumin ${CUMIN_HOME}/etc
	install -d ${CUMIN_HOME}/log
	install -d ${CUMIN_HOME}/rpc-defs/aviary
	install -pm 0644 ../sage/rpc-defs/aviary/* ${CUMIN_HOME}/rpc-defs/aviary
	bin/install-python-code python ${CUMIN_HOME}/python
	bin/install-python-code ../wooly/python ${CUMIN_HOME}/python 
	bin/install-python-code ../rosemary/python ${CUMIN_HOME}/python 
	bin/install-python-code ../mint/python ${CUMIN_HOME}/python 
	bin/install-python-code ../parsley/python ${CUMIN_HOME}/python
	bin/install-python-code ../sage/python ${CUMIN_HOME}/python
	find ${CUMIN_HOME} -type d

clean-version:
	-rm -f $(VERSION_FILE) 

write-version: clean-version
ifndef CUMIN_VERSION
	@echo svn info failed, version file not created, this is okay
else
	install -d $(CUMIN_HOME)
	echo $(CUMIN_VERSION) > $(VERSION_FILE)
	chmod 0644 $(VERSION_FILE)
endif

mark-local:
#if the file exists, allow the local mark to be applied
ifeq ($(shell ls $(VERSION_FILE) 2> /dev/null),$(VERSION_FILE))
	echo local >> $(VERSION_FILE)
endif

version: write-version

version-local: write-version mark-local

clean: clean-python-files clean-version

check:
	cumin-admin-test
	cumin-data-test
	cumin-web-test
