QPID_JMS_UPSTREAM_DIR := $(shell readlink -f upstreams/qpid-jms)
QPID_DISPATCH_UPSTREAM_DIR := $(shell readlink -f upstreams/qpid-dispatch)

ASCIIDOCTOR_OPTIONS := -a QpidJmsUpstreamDir="${QPID_JMS_UPSTREAM_DIR}" -a QpidDispatchUpstreamDir="${QPID_DISPATCH_UPSTREAM_DIR}"

BUILD_DIR := build

BOOK_SOURCES := $(shell find books -type f -name master.adoc)
BOOK_TARGETS := \
	${BOOK_SOURCES:books/%/master.adoc=${BUILD_DIR}/%/index.html} \
	${BOOK_SOURCES:books/%/master.adoc=${BUILD_DIR}/%/images}

IMAGE_SOURCES := $(shell find images -type f)
IMAGE_TARGETS := ${IMAGE_SOURCES:images/%=${BUILD_DIR}/images/%}

EXTRA_SOURCES := books/index.adoc
EXTRA_TARGETS := ${EXTRA_SOURCES:books/%.adoc=${BUILD_DIR}/%.html}

.PHONY: default
default: build

.PHONY: help
help:
	@echo "[default]      Equivalent to 'make build'"
	@echo "build          Renders the site to ${BUILD_DIR}/"
	@echo "clean          Removes ${BUILD_DIR}/ and other build artifacts"

.PHONY: build
build: ${BOOK_TARGETS} ${IMAGE_TARGETS} ${EXTRA_TARGETS}
	@echo "See the output in your browser at file://${PWD}/${BUILD_DIR}/index.html"

.PHONY: publish
publish: build
publish:
	rsync -av ${BUILD_DIR}/ file.rdu.redhat.com:public_html/acme-docs

.PHONY: clean
clean:
	rm -rf ${BUILD_DIR}

define BOOK_TEMPLATE =
$${BUILD_DIR}/${1}/index.html: $$(shell find -L books/${1} -type f -name \*.adoc)
	@mkdir -p $${@D}
	asciidoctor ${ASCIIDOCTOR_OPTIONS} -o $$@ books/${1}/master.adoc

$${BUILD_DIR}/${1}/images:
	@mkdir -p $${@D}
	ln -s --force --no-target-directory ../images $$@
endef

$(foreach dir,${BOOK_SOURCES:books/%/master.adoc=%},$(eval $(call BOOK_TEMPLATE,${dir})))

${BUILD_DIR}/%.html: books/%.adoc
	@mkdir -p ${@D}
	asciidoctor ${ASCIIDOCTOR_OPTIONS} -o $@ $<

${BUILD_DIR}/images/%: images/%
	@mkdir -p ${@D}
	cp $< $@
