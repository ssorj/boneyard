.PHONY: default render clean publish update-docbook update-input update-html clean-html clean-input

DOCBOOK_INPUT_FILES := $(wildcard docbook/*/*.xml)
HTML_INPUT_FILES := $(wildcard html/*/*.html)
MARKDOWN_INPUT_FILES := $(wildcard input/*/*.md)

default: render

render: clean
	transom input output

clean:
	rm -rf output

publish: TAG := "head"
publish: render
	rsync --delete -av output/ jross@people.apache.org:public_html/cistern/${TAG}

update-docbook:
	rm -rf docbook
	svn export "https://svn.apache.org/repos/asf/qpid/java/trunk/doc/book/src/java-broker/" docbook/java-broker
	svn export "https://svn.apache.org/repos/asf/qpid/java/trunk/doc/book/src/jms-client-0-8/" docbook/jms-client-0-8
	svn export "https://svn.apache.org/repos/asf/qpid/trunk/qpid/doc/book/src/cpp-broker/" docbook/cpp-broker
	svn export "https://svn.apache.org/repos/asf/qpid/trunk/qpid/doc/book/src/programming/" docbook/programming

update-html: clean-html ${DOCBOOK_INPUT_FILES:docbook/%.xml=html/%.html}

clean-html:
	rm -rf html

update-input: clean-input ${HTML_INPUT_FILES:html/%.html=input/%.md}

clean-input:
	rm -rf input

html/%.html: docbook/%.xml
	mkdir -p $$(dirname $@)
	pandoc --from docbook --to html5 --number-sections --output $@ $<

input/%.md: html/%.html
	mkdir -p $$(dirname $@)
	pandoc --from html --to markdown-header_attributes-definition_lists+pipe_tables-simple_tables-grid_tables-table_captions+footnotes --atx-headers --ascii --output $@ $<
