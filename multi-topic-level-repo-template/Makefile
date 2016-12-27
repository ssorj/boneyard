BUILD_DIR := build

BOOK_SOURCES := $(shell find books -type f -name master.adoc)
BOOK_TARGETS := \
	${BOOK_SOURCES:books/%/master.adoc=${BUILD_DIR}/%/index.html} \
	${BOOK_SOURCES:books/%/master.adoc=${BUILD_DIR}/%/images}

IMAGE_SOURCES := $(shell find images -type f)
IMAGE_TARGETS := ${IMAGE_SOURCES:images/%=${BUILD_DIR}/images/%}

EXTRA_TARGETS :=

.PHONY: default
default: build

.PHONY: help
help:
	@echo "[default]      Equivalent to 'make build'"
	@echo "build          Renders the site to build/"
	@echo "clean          Removes build/ and other build artifacts"

.PHONY: build
build: ${BOOK_TARGETS} ${IMAGE_TARGETS} ${EXTRA_TARGETS}
	find build -name \*.html

.PHONY: clean
clean:
	rm -rf ${BUILD_DIR}

define BOOK_TEMPLATE =
$${BUILD_DIR}/${1}/index.html: $$(shell find -L books/${1} -type f -name \*.adoc)
	@mkdir -p $${@D}
	asciidoctor -o $$@ books/${1}/master.adoc

$${BUILD_DIR}/${1}/images:
	@mkdir -p $${@D}
	ln -s ../../images $$@
endef

$(foreach dir,${BOOK_SOURCES:books/%/master.adoc=%},$(eval $(call BOOK_TEMPLATE,${dir})))

${BUILD_DIR}/images/%: images/%
	@mkdir -p ${@D}
	cp $< $@
