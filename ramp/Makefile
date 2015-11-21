# sudo yum install fop docbook-dtds docbook-style-xsl libxslt libxml2 epydoc

.PHONY: default release-notes docs clean

RELEASE := 0.22
JQL_QUERY := "project = 'qpid' and fixVersion in ('0.21', '0.22') and fixVersion not in ('0.20')"

default:	
	@echo "release-notes"
	@echo "docs"
	@echo "clean"

release-notes: output/release_notes_${RELEASE}.html.content

docs: output/site

data/tickets.xml: scripts/fetch-tickets.py
	mkdir -p data
	scripts/fetch-tickets.py ${JQL_QUERY} $@

data/tickets.db: data/tickets.xml scripts/import-tickets.py
	mkdir -p data
	scripts/import-tickets.py $< $@

output/release_notes_${RELEASE}.html.content: data/tickets.db
	mkdir -p output
	scripts/render-release-notes.py $< $@.tmp
	xmllint --html --format --output $@ $@.tmp
	rm $@.tmp

output/site:
	mkdir -p output/site
	scripts/generate-docs.sh ~/code/qpid-${RELEASE} ${RELEASE} $@

clean:
	rm -rf output
