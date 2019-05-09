.PHONY: build
build:
	sudo docker build --tag docker.io/ssorj/trainee .

.PHONY: run
run:
	sudo docker run -it -p 0.0.0.0:10001:22 ssorj/trainee

.PHONY: push
push:
	sudo docker push docker.io/ssorj/trainee:latest
