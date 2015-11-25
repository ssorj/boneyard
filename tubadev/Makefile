SUBDIRS = butyl wheaty smoky lentil tuba tuba-recorder wooly tuba-web

.PHONY: prepare build clean ${SUBDIRS}

build: clean prepare ${SUBDIRS}

${SUBDIRS}:
	${MAKE} -C $@

tuba-recorder: tuba

tuba-web: wooly tuba

tuba: lentil smoky

smoky wooly: wheaty

wheaty lentil smoky: butyl

clean:
	rm -rf ${TUBADEV_BUILD}

prepare:
	mkdir -p ${TUBADEV_BUILD}/bin
	mkdir -p ${TUBADEV_BUILD}/classes
	mkdir -p ${TUBADEV_BUILD}/jars
	mkdir -p ${TUBADEV_BUILD}/lib
	mkdir -p ${TUBADEV_BUILD}/conf
	mkdir -p ${TUBADEV_BUILD}/recordings
	mkdir -p ${TUBADEV_BUILD}/data
	mkdir -p ${TUBADEV_BUILD}/log
