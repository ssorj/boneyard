.NOTPARALLEL:

.PHONY: build
build:
	sudo docker build -t ssorj/files-http .

.PHONY: run
run:
	sudo docker run --rm --user 9999 -p 8080:8080 ssorj/files-http

.PHONY: debug
debug:
	sudo docker run --rm --user 9999 -p 8080:8080 -it ssorj/files-http /bin/bash

.PHONY: push
push:
	sudo docker push ssorj/files-http

# To tell the cluster about the new image:
#
# oc tag --source=docker ssorj/files-http:latest files-http:latest
