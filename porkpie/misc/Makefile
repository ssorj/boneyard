SOURCES := $(shell find specs -type f -name \*.spec.in)
TARGETS := ${SOURCES:specs/%.spec.in=%}

.PHONY: build
build: ${TARGETS}

.PHONY: clean
clean:
	rm -rf build

.PHONY: publish
publish: build
	rsync -av --delete build/SRPMS/* jross@alpha.ssorj.net:www/porkpie/
	for srpm in build/SRPMS/*; do echo "http://alpha.ssorj.net/porkpie/$${srpm#build/SRPMS/}"; done

define PACKAGE_TEMPLATE =
.PHONY: ${1}
${1}: build/SPECS/${1}.spec

build/SPECS/${1}.spec: specs/${1}.spec.in
	@mkdir -p build/SPECS build/SOURCES
	scripts/github-get-head-revision ssorj ${1} > build/${1}.revision
	scripts/configure-file $$< $$@ commit `cat build/${1}.revision`
	scripts/github-get-tarball ssorj ${1} `cat build/${1}.revision` \
		build/SOURCES/${1}-`cat build/${1}.revision`.tar.gz
	rpmbuild -D "_topdir $${PWD}/build" -bs $$@
endef

$(foreach target,${TARGETS},$(eval $(call PACKAGE_TEMPLATE,${target})))
