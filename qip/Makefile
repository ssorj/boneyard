.PHONY: build clean publish

files := \
	output/index.html \
	output/notes.html \
	output/qip-template.html \
	output/draft/qpid-improvement-process.html \
	output/draft/producer-flowcontrol-0.10.html \
	output/draft/jca-adapter.html \
	output/draft/message-groups.html \

build: ${files}

clean:
	rm -rf output index.md

publish:
	ssh root@jross.usersys.redhat.com "rm -rf /var/www/html/qip"
	scp -r output root@jross.usersys.redhat.com:/var/www/html/qip

index.md: index.md.in
	python index.py $< > $@

output/%.html: %.md template.html convert.py
	@mkdir -p output/draft tmp
	python convert.py $< template.html > $@
