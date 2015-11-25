.PHONY: build parser

build:
	${TUBADEV_JAVAC} src/wooly/*.java
	${TUBADEV_JAVAC} src/wooly/widgets/*.java
	${TUBADEV_JAVAC} src/wooly/lang/*.java
	${TUBADEV_JAVAC} src/wooly/server/*.java

parser:
	java javacc -output_directory=src/wooly/lang src/wooly/lang/*.jj
