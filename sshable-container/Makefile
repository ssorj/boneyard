.PHONY: build
build:
	podman build --tag docker.io/ssorj/trainee .

.PHONY: run
run:
	podman run -it -p 0.0.0.0:10001:22 ssorj/trainee

.PHONY: push
push:
	podman push docker.io/ssorj/trainee:latest
