DESTDIR := ""
PREFIX := /usr/local

.PHONY: build
build: electric-alibi

.PHONY: install
install: build
	mkdir -p ${DESTDIR}${PREFIX}/bin
	cp electric-alibi ${DESTDIR}${PREFIX}/bin/electric-alibi

.PHONY: clean
clean:
	rm -f electric-alibi

electric-alibi: electric-alibi.c
	gcc -I${PROTON_BUILD}/c/include -o $@ $< ${PROTON_BUILD}/c/libqpid-proton-core-static.a ${PROTON_BUILD}/c/libqpid-proton-proactor-static.a
