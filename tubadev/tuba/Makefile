.PHONY: build util runtime update datadirect capture dvb

build: datadirect dvb
	cp bin/* ${TUBADEV_BUILD}/bin

util:
	${TUBADEV_JAVAC} src/tuba/util/*.java
	${TUBADEV_JAVAC} src/tuba/util/mpeg/*.java

runtime: util
	${TUBADEV_JAVAC} src/tuba/runtime/*.java src/tuba/runtime/model/*.java
	cp src/tuba/runtime/*.sql ${TUBADEV_BUILD}/classes/tuba/runtime
	cp src/tuba/runtime/model/*.lentil ${TUBADEV_BUILD}/classes/tuba/runtime/model

update: runtime
	${TUBADEV_JAVAC} src/tuba/update/*.java

datadirect: update
	${TUBADEV_JAVAC} src/tuba/datadirect/xtvd/*.java
	cp src/tuba/datadirect/xtvd/*.xml ${TUBADEV_BUILD}/classes/tuba/datadirect/xtvd
	${TUBADEV_JAVAC} src/tuba/datadirect/*.java
	cp src/tuba/datadirect/*.xml ${TUBADEV_BUILD}/classes/tuba/datadirect

capture: runtime
	${TUBADEV_JAVAC} src/tuba/capture/*.java

dvb: capture
	gcc -Wall -I../../jdk/include -I../../jdk/include/linux -shared -o ${TUBADEV_BUILD}/lib/dvb.so src/tuba/dvb/Driver.c
	${TUBADEV_JAVAC} src/tuba/dvb/*.java
