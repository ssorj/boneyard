.PHONY: build
build: electric-alibi.spec clean build/SOURCES/electric-alibi-1.0.tar.gz build/SOURCES/qpid-proton-0.31.0.tar.gz
	rpmbuild -D "_topdir ${PWD}/build" -ba $<

build/SOURCES/electric-alibi-1.0.tar.gz:
	mkdir -p build/SOURCES build/tmp
	cd dist && make clean
	cp -a dist build/tmp/electric-alibi-1.0
	tar -C build/tmp -czf $@ electric-alibi-1.0

build/SOURCES/qpid-proton-0.31.0.tar.gz: qpid-proton-0.31.0.tar.gz
	mkdir -p build/SOURCES
	cp $< $@

.PHONY: clean
clean:
	rm -rf build
