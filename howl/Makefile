.PHONY: update clean

update: clean data/howl.mapping

clean:
	rm -rf data

data/howl.mapping: data/howl.log bin/generate-mapping
	mkdir -p data
	bin/generate-mapping $< > $@

data/howl.log: checkout
	mkdir -p data
	(cd checkout; git pull; git checkout origin/trunk; git --no-pager log > ${PWD}/$@)

checkout:
	git clone git://git.apache.org/qpid.git checkout
