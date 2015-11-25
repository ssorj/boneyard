.PHONY: build parser

build:
	${TUBADEV_JAVAC} src/lentil/*.java
	cp src/lentil/*.lentil ${TUBADEV_BUILD}/classes/lentil

parser:
	java javacc -output_directory=src/lentil src/lentil/*.jj
